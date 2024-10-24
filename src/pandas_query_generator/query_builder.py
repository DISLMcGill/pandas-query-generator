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
  def __init__(self, schema: Schema, query_structure: QueryStructure, multi_line: bool):
    self.schema: Schema = schema
    self.query_structure: QueryStructure = query_structure
    self.multi_line = multi_line
    self.operations: t.List[Operation] = []
    self.entity_name = random.choice(list(self.schema.entities.keys()))
    self.entity = self.schema.entities[self.entity_name]
    self.available_columns = list(self.entity.properties.keys())
    self.merged_columns: t.Dict[str, t.List[str]] = {}

  def build(self) -> Query:
    """
    Build a query based on the schema and query structure.

    Generates a random combination of query operations based on probabilities:
    - 50% chance of adding a selection operation
    - 50% chance of adding a projection operation
    - Random number of merge operations (0 to max_merges)
    - 50% chance of adding a group-by aggregation if allowed

    Returns:
      Query: A query object containing the generated operations.
    """
    if random.random() < 0.5:
      self.operations.append(self._generate_operation(Selection))

    if random.random() < 0.5:
      self.operations.append(self._generate_operation(Projection))

    for _ in range(random.randint(0, self.query_structure.max_merges)):
      self.operations.append(self._generate_operation(Merge))

    if self.query_structure.allow_groupby_aggregation and random.random() < 0.5:
      self.operations.append(self._generate_operation(GroupByAggregation))

    return Query(self.entity_name, self.operations, self.multi_line)

  def _generate_operation(self, operation: t.Type[Operation]) -> Operation:
    """
    Generate a specific type of query operation.

    This method acts as a factory for creating different types of query operations.
    It delegates the actual generation to type-specific methods based on the
    operation type requested.

    Args:
      operation: The type of operation to generate (Selection, Projection, etc.).

    Returns:
      Operation: The generated operation instance.

    Raises:
      ValueError: If an unsupported operation type is provided.
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
    Generate a selection (WHERE clause) operation.

    Creates a selection operation with random conditions based on the entity's
    property types. Handles different data types and operators appropriately:

    - Numeric (Int/Float): ==, !=, <, <=, >, >=
    - String: ==, !=, .str.startswith
    - Enum: ==, !=, .isin
    - Date: ==, !=, <, <=, >, >=

    Conditions are combined using randomly chosen logical operators (&, |).

    Returns:
      Operation: A Selection operation with randomly generated conditions.
    """
    conditions = []

    num_conditions = random.randint(1, self.query_structure.max_selection_conditions)

    for i in range(num_conditions):
      column = random.choice(list(self.available_columns))

      prop = self.entity.properties[column]

      next_op = random.choice(['&', '|']) if i < num_conditions - 1 else '&'

      match prop:
        case PropertyInt(min, max) | PropertyFloat(min, max):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = random.uniform(min, max)
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
        case PropertyDate(min, max):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = f"'{random.choice([min, max]).isoformat()}'"
          conditions.append((f"'{column}'", op, value, next_op))

    return Selection(conditions)

  def _generate_projection(self) -> Operation:
    """
    Generate a projection (SELECT columns) operation.

    Creates a projection operation by randomly selecting a subset of columns
    from the available columns. The number of columns is randomly determined
    within the bounds specified by max_projection_columns.

    After generating the projection, updates available_columns to only include
    the projected columns, affecting subsequent operations.

    Returns:
      Operation: A Projection operation with randomly selected columns.
    """
    to_project = random.randint(1, self.query_structure.max_projection_columns)

    columns = random.sample(
      self.available_columns,
      min(len(self.available_columns), to_project),
    )

    self.available_columns = columns

    return Projection(columns)

  def _generate_merge(self) -> Operation:
    """
    Generate a merge (JOIN) operation.

    Creates a merge operation that joins the current entity with another entity
    based on their relationships defined in the schema. Handles both direct
    foreign key relationships and reverse relationships.

    Features:
    - Tracks columns from merged entities for join compatibility
    - Supports both single-column and multi-column joins
    - Falls back to primary key joins if no valid relationship is found
    - Recursively generates operations for the right side of the merge

    Returns:
      Operation: A Merge operation with appropriate join conditions.

    Raises:
      ValueError: If no valid entities are available for merging.
    """
    right_query_structure = QueryStructure(
      allow_groupby_aggregation=False,
      max_groupby_columns=self.query_structure.max_groupby_columns,
      max_merges=self.query_structure.max_merges - 1,
      max_projection_columns=self.query_structure.max_projection_columns,
      max_selection_conditions=self.query_structure.max_selection_conditions,
    )

    possible_right_entities = []

    # Track both local and merged columns for join compatibility
    all_available_columns = set(self.available_columns)
    for merged_cols in self.merged_columns.values():
      all_available_columns.update(merged_cols)

    # Check foreign key relationships with current entity
    for local_col, [foreign_col, foreign_table] in self.entity.foreign_keys.items():
      if local_col in all_available_columns:
        possible_right_entities.append((local_col, foreign_col, foreign_table))

    # Check reverse relationships
    for entity_name, entity in self.schema.entities.items():
      for local_col, [foreign_col, foreign_table] in entity.foreign_keys.items():
        if foreign_table == self.entity_name and foreign_col in all_available_columns:
          possible_right_entities.append((foreign_col, local_col, entity_name))

    # If no valid relationships found, use primary keys
    if not possible_right_entities:
      available_entities = [e for e in self.schema.entities.keys() if e != self.entity_name]

      if not available_entities:
        raise ValueError('No valid entities for merge')

      right_entity_name = random.choice(available_entities)
      left_on = self.entity.primary_key
      right_on = self.schema.entities[right_entity_name].primary_key
    else:
      left_on, right_on, right_entity_name = random.choice(possible_right_entities)

    # Create builder for right side of merge
    right_builder = QueryBuilder(self.schema, right_query_structure, self.multi_line)
    right_builder.entity_name = right_entity_name
    right_builder.entity = self.schema.entities[right_entity_name]
    right_builder.available_columns = list(right_builder.entity.properties.keys())

    # Build right query and track its columns
    right_query = right_builder.build()

    # If right query has projections, use those columns
    projected_columns = []
    for op in right_query.operations:
      if isinstance(op, Projection):
        projected_columns = op.columns
        break

    # If no projection, use all available columns
    if not projected_columns:
      projected_columns = right_builder.available_columns

    # Track columns from this merge
    self.merged_columns[right_entity_name] = projected_columns

    def format_join_columns(columns: t.List[str] | str | None):
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
    Generate a group-by aggregation operation.

    Creates a group-by operation with random columns and an aggregation function.
    The number of group-by columns is bounded by max_groupby_columns and
    available columns.

    Features:
    - Randomly selects columns to group by
    - Chooses from standard aggregation functions:
      - mean: Average of numeric columns
      - sum: Sum of numeric columns
      - min: Minimum values
      - max: Maximum values
      - count: Count of rows in each group

    Returns:
      Operation: A GroupByAggregation operation with selected columns and function.
    """
    group_columns = random.sample(
      self.available_columns,
      random.randint(1, min(self.query_structure.max_groupby_columns, len(self.available_columns))),
    )

    agg_function = random.choice(['mean', 'sum', 'min', 'max', 'count'])

    return GroupByAggregation(group_columns, agg_function)
