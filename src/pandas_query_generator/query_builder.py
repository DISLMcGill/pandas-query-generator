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

    We add at most 1 selection and 1 projection for each query.

    Returns:
      Query: The generated query.
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
    Generate a specific type of operation.

    This method serves as a dispatcher to call the appropriate generation
    method based on the type of operation requested.

    Args:
      operation (Type[Operation]): The type of operation to generate.

    Returns:
      Operation: The generated operation.

    Raises:
      ValueError: If an unknown operation type is provided.
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
    Generate a selection operation.

    This method creates a selection operation with random conditions based on
    the properties of the selected entity. It handles different property types
    (int, float, string, enum, date) and generates appropriate conditions for each.
    It also randomly selects operators ('&' or '|') between conditions.

    Returns:
      Operation: The generated selection operation.
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
    Generate a projection operation.

    This method creates a projection operation by randomly selecting a subset
    of columns from the available columns of the entity. The number of columns
    to project is also randomly determined, bounded by the maximum specified
    in the query structure.

    Returns:
      Operation: The generated projection operation.
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
    Generate a merge operation with improved column tracking.

    This updated version ensures column compatibility through nested merges by:
    1. Tracking columns from each merged entity
    2. Verifying join column availability
    3. Propagating available columns up the merge chain
    """
    right_query_structure = QueryStructure(
      allow_groupby_aggregation=False,
      max_groupby_columns=2,
      max_merges=self.query_structure.max_merges - 1,
      max_projection_columns=4,
      max_selection_conditions=2,
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
    Generate a group by and aggregation operation.

    This method creates a group by and aggregation operation by randomly selecting
    columns to group by and an aggregation function to apply. The number of columns
    to group by is bounded by the maximum specified in the query structure.

    Returns:
      Operation: The generated GroupByAggregation operation.
    """
    group_columns = random.sample(
      self.available_columns,
      random.randint(1, min(self.query_structure.max_groupby_columns, len(self.available_columns))),
    )

    agg_function = random.choice(['mean', 'sum', 'min', 'max', 'count'])

    return GroupByAggregation(group_columns, agg_function)
