import random
import typing as t

from .entity import *
from .group_by import GroupByAggregation
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

  def build(self) -> Query:
    """
    Build a query based on the schema and query structure.

    We add at most 1 selection and 1 projection for each query.

    Returns:
      Query: The generated query.
    """
    if random.random() < 0.5:
      self._add_operation(self._generate_operation(Selection))

    if random.random() < 0.5:
      self._add_operation(self._generate_operation(Projection))

    for _ in range(random.randint(0, self.query_structure.max_merges)):
      self._add_operation(self._generate_operation(Merge))

    if self.query_structure.allow_groupby_aggregation and random.random() < 0.5:
      self._add_operation(self._generate_operation(GroupByAggregation))

    return Query(self.entity_name, self.operations, self.multi_line)

  def _add_operation(self, operation: Operation) -> None:
    """
    Add an operation to the list of operations for this query.

    Args:
      operation (Operation): The operation to add to the query.
    """
    self.operations.append(operation)

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

    for _ in range(num_conditions):
      column = random.choice(list(self.available_columns))

      prop = self.entity.properties[column]

      match prop:
        case PropertyInt(min, max) | PropertyFloat(min, max):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = random.uniform(min, max)
          if isinstance(prop, PropertyInt):
            value = int(value)
        case PropertyString(starting_character):
          op = random.choice(['==', '!=', '.str.startswith'])
          value = random.choice(starting_character)
          value = f"'{value}'"  # Wrap string values in quotes
        case PropertyEnum(values):
          op = random.choice(['==', '!=', '.isin'])
          if op == '.isin':
            value = random.sample(values, random.randint(1, len(values)))
          else:
            value = random.choice(values)
        case PropertyDate(min, max):
          op = random.choice(['==', '!=', '<', '<=', '>', '>='])
          value = f"'{random.choice([min, max]).isoformat()}'"

      # Select the operator for the next condition (ignored for the last condition)
      next_op = random.choice(['&', '|'])

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
    Generate a merge operation.

    This method creates a merge operation by selecting a right entity to merge with,
    determining the columns to join on, and generating a sub-query for the right side
    of the merge. It handles cases where foreign key relationships exist and falls back
    to random entity selection if no such relationships are found.

    Returns:
      Operation: The generated merge operation.
    """
    right_query_structure = QueryStructure(
      allow_groupby_aggregation=False,
      allow_projection=True,
      max_groupby_columns=2,
      max_merges=1,
      max_projection_columns=4,
      max_selection_conditions=2,
    )

    possible_right_entities = []

    for local_col, [foreign_col, foreign_table] in self.entity.foreign_keys.items():
      possible_right_entities.append((local_col, foreign_col, foreign_table))

    for entity_name, entity in self.schema.entities.items():
      for local_col, [foreign_col, foreign_table] in entity.foreign_keys.items():
        if foreign_table == self.entity_name:
          possible_right_entities.append((foreign_col, local_col, entity_name))

    if not possible_right_entities:
      right_entity_name = random.choice(
        [e for e in self.schema.entities.keys() if e != self.entity_name]
      )

      left_on = self.entity.primary_key
      right_on = self.schema.entities[right_entity_name].primary_key
    else:
      left_on, right_on, right_entity_name = random.choice(possible_right_entities)

    right_builder = QueryBuilder(self.schema, right_query_structure, self.multi_line)

    right_builder.entity_name = right_entity_name
    right_builder.entity = self.schema.entities[right_entity_name]
    right_builder.available_columns = list(right_builder.entity.properties.keys())

    right_query = right_builder.build()

    return Merge(
      right=Query(right_query.entity, right_query.operations, self.multi_line),
      left_on=left_on,
      right_on=right_on,
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
