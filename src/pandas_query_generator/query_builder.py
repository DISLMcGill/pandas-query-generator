import random
import typing as t

from .entity import PropertyDate, PropertyEnum, PropertyFloat, PropertyInt, PropertyString
from .group_by_aggregation import GroupByAggregation
from .merge import Merge
from .operation import Operation
from .projection import Projection
from .query import Query
from .query_structure import QueryStructure
from .schema import Schema
from .selection import Selection


class QueryBuilder:
  """
  A builder class for generating random, valid pandas DataFrame queries.

  This class constructs queries using a combination of operations like selection,
  projection, merge, and group by aggregation. It ensures that generated queries
  are valid by tracking available columns and maintaining referential integrity.

  Attributes:
    schema (Schema): The database schema containing entity definitions.
    query_structure (QueryStructure): Configuration parameters for query generation.
    multi_line (bool): Whether to format queries across multiple lines.
    operations (List[Operation]): List of operations to be applied in the query.
    entity_name (str): Name of the current entity being queried.
    entity (Entity): The current entity's schema definition.
    current_columns (Set[str]): Set of columns currently available for operations.
    required_columns (Set[str]): Columns that must be preserved (e.g., join keys).
  """

  def __init__(self, schema: Schema, query_structure: QueryStructure, multi_line: bool):
    self.schema: Schema = schema
    self.query_structure: QueryStructure = query_structure
    self.multi_line = multi_line
    self.operations: t.List[Operation] = []
    self.entity_name = random.choice(list(self.schema.entities.keys()))
    self.entity = self.schema.entities[self.entity_name]
    self.current_columns = set(self.entity.properties.keys())
    self.required_columns: t.Set[str] = set()  # Columns that must be preserved

  def build(self) -> Query:
    """
    Build a complete query by randomly combining different operations.

    The method generates operations based on the following probabilities:
    - 50% chance of adding a selection (WHERE clause)
    - 50% chance of adding a projection (SELECT columns)
    - 0 to max_merges joins with other tables
    - 50% chance of adding a group by if grouping is enabled

    Each operation is validated to ensure it uses only available columns
    and maintains referential integrity.

    Returns:
      Query: A complete, valid query object with all generated operations.
    """
    if self.query_structure.max_selection_conditions > 0 and random.random() < 0.5:
      self.operations.append(self._generate_operation(Selection))

    if self.query_structure.max_projection_columns > 0 and random.random() < 0.5:
      self.operations.append(self._generate_operation(Projection))

    for _ in range(random.randint(0, self.query_structure.max_merges)):
      try:
        self.operations.append(self._generate_operation(Merge))
      except ValueError:
        break

    if (
      self.query_structure.max_groupby_columns > 0
      and random.random() < 0.5
      and self.current_columns
    ):
      self.operations.append(self._generate_operation(GroupByAggregation))

    return Query(self.entity_name, self.operations, self.multi_line, self.current_columns)

  def _generate_operation(self, operation: t.Type[Operation]) -> Operation:
    """
    Factory method to create specific types of query operations.

    Routes the operation creation to the appropriate specialized method based
    on the operation type requested. Each specialized method handles the
    validation and generation logic specific to that operation type.

    Args:
      operation: The type of operation to generate (Selection, Projection, etc.)

    Returns:
      Operation: A newly generated operation of the requested type.

    Raises:
      ValueError: If the operation type is not supported or generation fails.
    """
    if operation == Selection:
      return self._generate_selection()
    elif operation == Projection:
      return self._generate_projection()
    elif operation == Merge:
      return self._generate_merge()
    elif operation == GroupByAggregation:
      return self._generate_group_by_aggregation()
    else:
      raise ValueError(f'Unknown operation type: {operation}')

  def _generate_selection(self) -> Operation:
    """
    Generate a WHERE clause for filtering rows.

    Creates conditions for filtering data based on column types:
    - Numeric columns: Comparison operators (==, !=, <, <=, >, >=)
    - String columns: Equality, inequality, and string operations
    - Enum columns: Value matching and set membership tests
    - Date columns: Date comparison operations

    Conditions are combined using AND (&) or OR (|) operators. The number
    of conditions is bounded by max_selection_conditions configuration.

    Returns:
      Operation: A Selection operation with the generated conditions.
    """
    if not self.current_columns:
      return Selection([])

    num_conditions = random.randint(
      1, min(self.query_structure.max_selection_conditions, len(self.current_columns))
    )

    conditions, available_columns = [], list(self.current_columns)

    for i in range(num_conditions):
      column = random.choice(available_columns)

      prop, next_op = (
        self.entity.properties[column],
        random.choice(['&', '|']) if i < num_conditions - 1 else '&',
      )

      match prop:
        case PropertyInt(minimum, maximum) | PropertyFloat(minimum, maximum):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = random.uniform(minimum, maximum)
          if isinstance(prop, PropertyInt):
            value = int(value)
          conditions.append((f"'{column}'", op, value, next_op))
        case PropertyString(starting_character):
          op = random.choice(['==', '!=', '.str.startswith'])
          value = random.choice(starting_character)
          quoted_value = f"'{value}'" if "'" not in value else f'"{value}"'
          conditions.append((f"'{column}'", op, quoted_value, next_op))
        case PropertyEnum(values):
          op = random.choice(['==', '!=', '.isin'])
          if op == '.isin':
            selected_values = random.sample(values, random.randint(1, len(values)))
            quoted_values = [f"'{v}'" if "'" not in v else f'"{v}"' for v in selected_values]
            value = f"[{', '.join(quoted_values)}]"
          else:
            value = random.choice(values)
            value = f"'{value}'" if "'" not in value else f'"{value}"'
          conditions.append((f"'{column}'", op, value, next_op))
        case PropertyDate(minimum, maximum):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = f"'{random.choice([minimum, maximum]).isoformat()}'"
          conditions.append((f"'{column}'", op, value, next_op))

    return Selection(conditions)

  def _generate_projection(self) -> Operation:
    """
    Generate a SELECT clause for choosing columns.

    Randomly selects a subset of available columns while ensuring that
    required columns (like join keys) are always included. The number
    of selected columns is bounded by max_projection_columns configuration.

    The operation updates the available columns for subsequent operations
    while maintaining required columns for joins and other operations.

    Returns:
      Operation: A Projection operation with the selected columns.
    """
    available_for_projection = self.current_columns - self.required_columns

    if not available_for_projection:
      # If no columns available for projection besides required ones,
      # project all current columns
      return Projection(list(self.current_columns))

    to_project = random.randint(
      1, min(self.query_structure.max_projection_columns, len(available_for_projection))
    )

    # Select random columns plus required columns
    selected_columns = random.sample(list(available_for_projection), to_project)
    columns = list(set(selected_columns) | self.required_columns)

    # Update available columns but ensure required ones stay
    self.current_columns = set(columns)

    return Projection(columns)

  def _generate_merge(self) -> Operation:
    """
    Generate a JOIN operation with another table.

    Creates a join operation based on foreign key relationships defined
    in the schema. Ensures join columns are preserved in projections on
    both sides of the join.

    The method:

    1. Identifies possible join relationships
    2. Randomly selects a valid join path
    3. Creates a new query for the right side
    4. Ensures join columns are preserved

    Returns:
      Operation: A Merge operation with the join conditions.

    Raises:
      ValueError: If no valid join relationships are available.
    """
    right_query_structure = QueryStructure(
      max_groupby_columns=0,
      max_merges=self.query_structure.max_merges - 1,
      max_projection_columns=self.query_structure.max_projection_columns,
      max_selection_conditions=self.query_structure.max_selection_conditions,
    )

    possible_right_entities = []

    # Find all possible join relationships
    for local_col, [foreign_col, foreign_table] in self.entity.foreign_keys.items():
      if local_col in self.current_columns:
        possible_right_entities.append((local_col, foreign_col, foreign_table))

    if not possible_right_entities:
      raise ValueError('No valid entities for merge')
    else:
      left_on, right_on, right_entity_name = random.choice(possible_right_entities)

    # Create builder for right side query
    right_builder = QueryBuilder(self.schema, right_query_structure, self.multi_line)
    right_builder.entity_name = right_entity_name
    right_builder.entity = self.schema.entities[right_entity_name]
    right_builder.current_columns = set(right_builder.entity.properties.keys())

    # Ensure join column is preserved
    right_builder.required_columns.add(right_on)

    # Update our current columns on this query
    right_query = right_builder.build()
    self.current_columns = right_query.available_columns

    def format_join_columns(columns: str | t.List[str]) -> str:
      return (
        f"[{', '.join(f"'{col}'" for col in columns)}]"
        if isinstance(columns, list)
        else f"'{columns}'"
      )

    return Merge(
      right=right_query,
      left_on=format_join_columns(left_on),
      right_on=format_join_columns(right_on),
    )

  def _generate_group_by_aggregation(self) -> Operation:
    """
    Generate a GROUP BY clause with aggregation.

    Creates a grouping operation that:
    1. Randomly selects columns to group by
    2. Chooses an aggregation function (mean, sum, min, max, count)
    3. Ensures numeric_only parameter is set appropriately

    The number of grouping columns is bounded by max_groupby_columns
    configuration and available columns.

    Returns:
      Operation: A GroupByAggregation operation with the grouping
      configuration.
    """
    if not self.current_columns:
      return GroupByAggregation([], 'count')

    group_columns = random.sample(
      list(self.current_columns),
      random.randint(1, min(self.query_structure.max_groupby_columns, len(self.current_columns))),
    )

    agg_function = random.choice(['mean', 'sum', 'min', 'max', 'count'])

    return GroupByAggregation(group_columns, agg_function)
