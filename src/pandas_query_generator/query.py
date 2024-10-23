import typing as t
from dataclasses import dataclass

from .group_by import GroupByAggregation
from .merge import Merge
from .operation import Operation
from .projection import Projection
from .selection import Selection


@dataclass
class Query:
  """
  Builds a query based on the given schema and query structure.
  """

  entity: str
  operations: t.List[Operation]
  multi_line: bool

  def __str__(self) -> str:
    return (
      self.format_multi_line()[0]
      if self.multi_line
      else f'{self.entity}{''.join(op.apply(self.entity) for op in self.operations)}'
    )

  def format_multi_line(self, start_counter: int = 1) -> t.Tuple[str, int]:
    lines = []

    df_counter, current_df = start_counter, self.entity

    for op in self.operations:
      if isinstance(op, (Selection, Projection, GroupByAggregation)):
        lines.append(f'df{df_counter} = {current_df}{op.apply(current_df)}')
      elif isinstance(op, Merge):
        right_query, next_counter = op.right.format_multi_line(df_counter + 1)
        lines.extend(right_query.split('\n'))
        lines.append(
          f"df{next_counter} = {current_df}.merge(df{next_counter-1}, left_on='{op.left_on}', right_on='{op.right_on}')"
        )
        df_counter = next_counter

      current_df, df_counter = f'df{df_counter}', df_counter + 1

    return '\n'.join(lines), df_counter
