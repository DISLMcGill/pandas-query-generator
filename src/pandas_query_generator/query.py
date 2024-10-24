import typing as t

from .group_by_aggregation import GroupByAggregation
from .merge import Merge
from .operation import Operation
from .projection import Projection
from .selection import Selection


class Query:
  """
  Represents a complete database query with tracking for query complexity.

  A query consists of a target entity and a sequence of operations to be
  applied to that entity. Query complexity is determined primarily by the
  number of merge operations and their nesting depth.

  Attributes:
    entity (str): The name of the target entity.
    operations (List[Operation]): List of operations to apply.
    multi_line (bool): Whether to format output across multiple lines.
    available_columns (Set[str]): Columns available for operations.
    complexity (int): Measure of query complexity based on merge operations.
  """

  def __init__(
    self,
    entity: str,
    operations: t.List[Operation],
    multi_line: bool,
    available_columns: t.Set[str],
  ):
    self.entity = entity
    self.operations = operations
    self.multi_line = multi_line
    self.available_columns = available_columns
    self.complexity = self._calculate_complexity()

  def __str__(self) -> str:
    return (
      self.format_multi_line()[0]
      if self.multi_line
      else f'{self.entity}{''.join(op.apply(self.entity) for op in self.operations)}'
    )

  def __lt__(self, other: 'Query') -> bool:
    """Less than comparison based on complexity and string representation."""
    return (self.complexity, str(self)) < (other.complexity, str(other))

  def __le__(self, other: 'Query') -> bool:
    """Less than or equal comparison based on complexity and string representation."""
    return (self.complexity, str(self)) <= (other.complexity, str(other))

  def __gt__(self, other: 'Query') -> bool:
    """Greater than comparison based on complexity and string representation."""
    return (self.complexity, str(self)) > (other.complexity, str(other))

  def __ge__(self, other: 'Query') -> bool:
    """Greater than or equal comparison based on complexity and string representation."""
    return (self.complexity, str(self)) >= (other.complexity, str(other))

  def _calculate_complexity(self) -> int:
    """
    Calculate query complexity based on merge operations.

    Complexity is determined by:
    1. Number of top-level merges
    2. Recursive complexity of nested merges
    3. Additional weight for deeply nested structures

    Returns:
      int: Complexity score for the query
    """

    def get_merge_complexity(op: Operation) -> int:
      if isinstance(op, Merge):
        nested_complexity = sum(
          get_merge_complexity(nested_op) for nested_op in op.right.operations
        )
        return 1 + nested_complexity
      return 0

    return sum(get_merge_complexity(op) for op in self.operations)

  def format_multi_line(self, start_counter: int = 1) -> t.Tuple[str, int]:
    lines = []
    df_counter = start_counter
    current_df = self.entity

    for op in self.operations:
      if isinstance(op, (Selection, Projection, GroupByAggregation)):
        lines.append(f'df{df_counter} = {current_df}{op.apply(current_df)}')
        current_df = f'df{df_counter}'
        df_counter += 1
      elif isinstance(op, Merge):
        right_statements, right_final_counter = op.right.format_multi_line(df_counter)

        if right_statements:
          lines.extend(right_statements.split('\n'))

        right_df = f'df{right_final_counter-1}'

        lines.append(
          f'df{right_final_counter} = {current_df}.merge({right_df}, '
          f'left_on={op.left_on}, right_on={op.right_on})'
        )

        current_df = f'df{right_final_counter}'
        df_counter = right_final_counter + 1

    return '\n'.join(lines), df_counter
