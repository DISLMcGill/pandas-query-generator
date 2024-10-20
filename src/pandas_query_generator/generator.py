import random
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta

import pandas as pd
from entity import *
from query_structure import QueryStructure
from schema import Schema


@dataclass
class Operation(ABC):
  entity: str

  @abstractmethod
  def __str__(self) -> str:
    pass

  @abstractmethod
  def apply(self, var_name: str) -> str:
    pass

  @abstractmethod
  def __eq__(self, other) -> bool:
    pass


@dataclass
class Selection(Operation):
  conditions: t.List[t.Tuple[str, str, t.Any]]  # [(column, operator, value), ...]

  def __str__(self) -> str:
    conditions = ' & '.join(
      f"({self.entity}['{col}'] {op} {repr(val)})" for col, op, val in self.conditions
    )
    return f'{self.entity}[{conditions}]'

  def apply(self, var_name: str) -> str:
    conditions = ' & '.join(
      f"({var_name}['{col}'] {op} {repr(val)})" for col, op, val in self.conditions
    )
    return f'{var_name} = {var_name}[{conditions}]'

  def __eq__(self, other) -> bool:
    if not isinstance(other, Selection):
      return False
    return self.entity == other.entity and self.conditions == other.conditions


@dataclass
class Projection(Operation):
  columns: t.List[str]

  def __str__(self) -> str:
    columns = ', '.join(f"'{col}'" for col in self.columns)
    return f'{self.entity}[[{columns}]]'

  def apply(self, var_name: str) -> str:
    columns = ', '.join(f"'{col}'" for col in self.columns)
    return f'{var_name} = {var_name}[[{columns}]]'

  def __eq__(self, other) -> bool:
    if not isinstance(other, Projection):
      return False
    return self.entity == other.entity and set(self.columns) == set(other.columns)


@dataclass
class Merge(Operation):
  right_entity: str
  left_on: str
  right_on: str

  def __str__(self) -> str:
    return f"{self.entity}.merge({self.right_entity}, left_on='{self.left_on}', right_on='{self.right_on}')"

  def apply(self, var_name: str) -> str:
    return f"{var_name} = {var_name}.merge({self.right_entity}, left_on='{self.left_on}', right_on='{self.right_on}')"

  def __eq__(self, other) -> bool:
    if not isinstance(other, Merge):
      return False
    return (
      self.entity == other.entity
      and self.right_entity == other.right_entity
      and self.left_on == other.left_on
      and self.right_on == other.right_on
    )


@dataclass
class GroupByAggregate(Operation):
  group_columns: t.List[str]
  agg_dict: t.Dict[str, str]  # {column: agg_function}

  def __str__(self) -> str:
    group_columns = ', '.join(f"'{col}'" for col in self.group_columns)
    agg_str = ', '.join(f"'{col}': '{func}'" for col, func in self.agg_dict.items())
    return f'{self.entity}.groupby([{group_columns}]).agg({{{agg_str}}})'

  def apply(self, var_name: str) -> str:
    group_columns = ', '.join(f"'{col}'" for col in self.group_columns)
    agg_str = ', '.join(f"'{col}': '{func}'" for col, func in self.agg_dict.items())
    return f'{var_name} = {var_name}.groupby([{group_columns}]).agg({{{agg_str}}})'

  def __eq__(self, other) -> bool:
    if not isinstance(other, GroupByAggregate):
      return False
    return (
      self.entity == other.entity
      and set(self.group_columns) == set(other.group_columns)
      and self.agg_dict == other.agg_dict
    )


@dataclass
class Query:
  operations: t.List[Operation] = field(default_factory=list)
  available_columns: t.Dict[str, t.Set[str]] = field(default_factory=dict)

  def __str__(self) -> str:
    if not self.operations:
      return ''

    # Start with the initial entity
    current_var = self.operations[0].entity
    query_lines = [current_var]

    # Build the query string
    for op in self.operations:
      query_line = op.apply(current_var)
      query_lines.append(query_line)
      current_var = current_var  # Variable name remains the same

    return '\n'.join(query_lines)

  def to_pandas_query(self) -> str:
    if not self.operations:
      return ''

    # Start with the initial entity
    current_var = self.operations[0].entity
    query_str = current_var

    # Build the query by chaining operations
    for op in self.operations:
      if isinstance(op, Selection):
        conditions = ' & '.join(
          f"({current_var}['{col}'] {operator} {repr(value)})"
          if operator in ['==', '!=', '>', '<', '>=', '<=']
          else f"({current_var}['{col}']{operator}{value})"
          for col, operator, value in op.conditions
        )
        query_str = f'{query_str}[{conditions}]'
      elif isinstance(op, Projection):
        columns = ', '.join(f"'{col}'" for col in op.columns)
        query_str = f'{query_str}[[{columns}]]'
      elif isinstance(op, Merge):
        query_str = (
          f"{query_str}.merge({op.right_entity}, left_on='{op.left_on}', right_on='{op.right_on}')"
        )
      elif isinstance(op, GroupByAggregate):
        group_columns = ', '.join(f"'{col}'" for col in op.group_columns)
        agg_dict_str = ', '.join(f"'{col}': '{func}'" for col, func in op.agg_dict.items())
        query_str = f'{query_str}.groupby(by=[{group_columns}]).agg({{{agg_dict_str}}})'

    return query_str

  def add_operation(self, operation: Operation) -> bool:
    # Avoid adding a duplicate operation to the previous one
    if self.operations and operation in self.operations:
      return False  # Skip adding this operation as it's a duplicate

    self.operations.append(operation)

    # Update available columns after the operation
    if isinstance(operation, Projection):
      self.available_columns[operation.entity] = set(operation.columns)
    elif isinstance(operation, Merge):
      if (
        operation.entity in self.available_columns
        and operation.right_entity in self.available_columns
      ):
        merged_entity = f'merged_{operation.entity}_{operation.right_entity}'
        self.available_columns[merged_entity] = self.available_columns[operation.entity].union(
          self.available_columns[operation.right_entity]
        )
    elif isinstance(operation, GroupByAggregate):
      self.available_columns[operation.entity] = set(
        operation.group_columns + list(operation.agg_dict.keys())
      )

    return False


class ForeignKeyGraph:
  def __init__(self, schema: Schema):
    self.graph: t.Dict[str, t.Dict[str, t.List[str]]] = {}

    for entity_name, entity in schema.entities.items():
      self.graph[entity_name] = entity.foreign_keys

  def find_merge_path(
    self, from_entity: str, to_entity: str
  ) -> t.Optional[t.List[t.Tuple[str, str, str]]]:
    path = []
    visited = set()

    def dfs(current: str) -> bool:
      if current == to_entity:
        return True
      visited.add(current)
      for fk, (_, ref_entity) in self.graph[current].items():
        if ref_entity not in visited:
          path.append((current, fk, ref_entity))
          if dfs(ref_entity):
            return True
          path.pop()
      visited.remove(current)
      return False

    return path if dfs(from_entity) else None


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema: Schema = schema
    self.query_structure: QueryStructure = query_structure
    self.foreign_key_graph = ForeignKeyGraph(schema)
    self.operation_weights = self._initialize_weights()

    self.entities_used = set()

    self.sample_data = {
      entity: self.schema.entities[entity].generate_dataframe() for entity in self.schema.entities
    }

  def generate(self, max_attempts=10) -> t.Optional[Query]:
    for _ in range(max_attempts):
      query = self._generate_single_query()
      if self._is_query_meaningful(query):
        return query
    return None

  def _initialize_weights(self) -> t.Dict[t.Type[Operation], float]:
    return {
      GroupByAggregate: 0.15  # at the end
      * self.query_structure.allow_aggregation
      * self.query_structure.allow_group_by,
      Merge: 0.3,  # RNG
      Projection: 0.2 * self.query_structure.allow_projection,  # RNG
      Selection: 0.3,  # RNG
    }

  def _generate_single_query(self) -> Query:
    query = Query()

    initial_entity = random.choice(list(self.schema.entities.keys()))

    self.entities_used.add(initial_entity)

    query.available_columns[initial_entity] = set(
      self.schema.entities[initial_entity].properties.keys()
    )

    max_operations, max_attempts = (
      self.query_structure.num_selections + self.query_structure.num_merges + 3,
      5000,
    )

    attempts = operations_performed = 0

    while operations_performed < max_operations and attempts < max_attempts:
      attempts += 1

      # Prioritize merge operations early in the query generation
      if operations_performed < 2 and len(self.entities_used) < len(self.schema.entities):
        operation_type = Merge
      else:
        operation_type = self._choose_operation()

      if self._can_perform_operation(query, operation_type):
        success = self._add_operation(query, initial_entity, operation_type)

        if success:
          operations_performed += 1
          self._adjust_weights(operation_type, query)

      if attempts >= max_attempts:
        break

    return query

  def _choose_operation(self) -> t.Type[Operation]:
    operations = list(self.operation_weights.keys())
    weights = list(self.operation_weights.values())
    return random.choices(operations, weights=weights, k=1)[0]

  def _can_perform_operation(self, query: Query, operation_type: t.Type[Operation]) -> bool:
    if operation_type == Selection:
      return self._can_perform_selection(query)
    elif operation_type == Projection:
      return self._can_perform_projection(query)
    elif operation_type == Merge:
      return self._can_perform_merge(query)
    elif operation_type == GroupByAggregate:
      return self._can_perform_group_by_aggregate(query)
    return False

  def _add_operation(
    self, query: Query, current_entity: str, operation_type: t.Type[Operation]
  ) -> bool:
    if operation_type == Selection:
      return self._add_selection(query, current_entity)
    elif operation_type == Projection:
      return self._add_projection(query, current_entity)
    elif operation_type == Merge:
      return self._add_merge(query, current_entity)
    elif operation_type == GroupByAggregate:
      return self._add_group_by_aggregate(query, current_entity)
    return False

  def _can_perform_selection(self, query: Query) -> bool:
    return (
      len([op for op in query.operations if isinstance(op, Selection)])
      < self.query_structure.num_selections
    )

  def _can_perform_projection(self, _: Query) -> bool:
    return self.query_structure.allow_projection

  def _can_perform_merge(self, query: Query) -> bool:
    return (
      len([op for op in query.operations if isinstance(op, Merge)])
      < self.query_structure.num_merges
    )

  def _can_perform_group_by_aggregate(self, query: Query) -> bool:
    return self.query_structure.allow_aggregation and not any(
      isinstance(op, GroupByAggregate) for op in query.operations
    )

  def _add_selection(self, query: Query, current_entity: str) -> bool:
    available_columns = query.available_columns[current_entity]

    if not available_columns:
      return False

    column = random.choice(list(available_columns))
    property = self.schema.entities[current_entity].properties[column]
    operator, value = self._generate_condition(property)
    selection_op = Selection(current_entity, [(column, operator, value)])

    return query.add_operation(selection_op)

  def _add_projection(self, query: Query, current_entity: str) -> bool:
    available_columns = query.available_columns[current_entity]

    if not available_columns:
      return False

    num_cols = random.randint(1, len(available_columns))
    selected_columns = random.sample(list(available_columns), num_cols)
    projection_op = Projection(current_entity, selected_columns)

    return query.add_operation(projection_op)

  def _add_merge(self, query: Query, current_entity: str) -> bool:
    available_entities = set(self.schema.entities.keys()) - self.entities_used

    if not available_entities:
      return False

    target_entity = random.choice(list(available_entities))
    merge_path = self.foreign_key_graph.find_merge_path(current_entity, target_entity)

    if merge_path:
      success = self._add_merge_with_path(query, merge_path)
    else:
      success = self._add_merge_without_path(query, current_entity, target_entity)

    if success:
      self.entities_used.add(target_entity)

    return success

  def _add_merge_with_path(self, query: Query, merge_path: t.List[t.Tuple[str, str, str]]) -> bool:
    for left_entity, left_key, right_entity in merge_path:
      if left_key in self.schema.entities[left_entity].foreign_keys:
        right_key = self.schema.entities[left_entity].foreign_keys[left_key][1]
      else:
        right_key = next(
          (
            k
            for k, v in self.schema.entities[right_entity].foreign_keys.items()
            if v[0] == left_entity and v[1] == left_key
          ),
          None,
        )
        if right_key is None:
          continue

      merge_op = Merge(left_entity, right_entity, left_key, right_key)

      if not query.add_operation(merge_op):
        return False

    return True

  def _add_merge_without_path(self, query: Query, left_entity: str, right_entity: str) -> bool:
    left_columns = query.available_columns[left_entity]
    right_columns = set(self.schema.entities[right_entity].properties.keys())

    # First, try to find common column names
    common_columns = left_columns.intersection(right_columns)

    if common_columns:
      merge_column = random.choice(list(common_columns))
      merge_op = Merge(left_entity, right_entity, merge_column, merge_column)
      return query.add_operation(merge_op)

    # If no common columns, try to find columns with similar names
    for left_col in left_columns:
      for right_col in right_columns:
        if left_col.lower() in right_col.lower() or right_col.lower() in left_col.lower():
          merge_op = Merge(left_entity, right_entity, left_col, right_col)
          return query.add_operation(merge_op)

    # If still no match, choose random columns as a last resort
    left_col = random.choice(list(left_columns))
    right_col = random.choice(list(right_columns))
    merge_op = Merge(left_entity, right_entity, left_col, right_col)
    return query.add_operation(merge_op)

  def _add_group_by_aggregate(self, query: Query, current_entity: str) -> bool:
    available_columns = query.available_columns[current_entity]

    if len(available_columns) < 2:  # Need at least one for grouping and one for aggregating
      return False

    group_cols = random.sample(
      list(available_columns), random.randint(1, len(available_columns) - 1)
    )

    agg_cols = list(available_columns - set(group_cols))
    agg_dict = {col: random.choice(['sum', 'mean', 'count', 'min', 'max']) for col in agg_cols}

    group_by_agg_op = GroupByAggregate(current_entity, group_cols, agg_dict)

    return query.add_operation(group_by_agg_op)

  def _generate_condition(self, property: Property) -> t.Tuple[str, t.Any]:
    operators = {
      PropertyInt: ['>', '<', '>=', '<=', '==', '!='],
      PropertyFloat: ['>', '<', '>=', '<='],  # Excluding '==' and '!=' for floats
      PropertyEnum: ['==', '!='],
      PropertyString: ['==', '!=', '.str.startswith', '.str.contains'],
      PropertyDate: ['>', '<', '>=', '<=', '==', '!='],
    }

    match property:
      case PropertyInt(min, max):
        operator = random.choice(operators[PropertyInt])
        value = random.randint(min, max)
        return operator, value
      case PropertyFloat(min, max):
        operator = random.choice(operators[PropertyFloat])
        value = round(random.uniform(min, max), 2)
        return operator, value
      case PropertyEnum(values):
        operator = random.choice(operators[PropertyEnum])
        value = random.choice(values)
        return operator, f"'{value}'"  # Wrapping in quotes for string comparison
      case PropertyString(starting_character):
        operator = random.choice(operators[PropertyString])
        if operator in ['.str.startswith', '.str.contains']:
          value = random.choice(starting_character)
          return operator, f"('{value}')"
        else:
          # Generate a random string starting with one of the starting characters
          value = random.choice(starting_character) + ''.join(
            random.choices('abcdefghijklmnopqrstuvwxyz', k=5)
          )
          return operator, f"'{value}'"
      case PropertyDate(min, max):
        operator = random.choice(operators[PropertyDate])
        days_between = (max - min).days
        random_days = random.randint(0, days_between)
        value = (min + timedelta(days=random_days)).strftime('%Y-%m-%d')
        return operator, f"'{value}'"

  def _is_query_meaningful(self, query: Query) -> bool:
    try:
      result = self._execute_query(query, self.sample_data)
      return result is not None and not result.empty
    except:
      return False

  def _execute_query(
    self, query: Query, test_data: t.Dict[str, pd.DataFrame]
  ) -> pd.DataFrame | None:
    full_query, environment = str(query), {**test_data}
    exec(full_query, globals(), environment)
    return environment.get(query.operations[0].entity, None)

  def _adjust_weights(self, operation_type: t.Type[Operation], query: Query):
    base_adjustment = 0.05

    operation_types = [type(op) for op in query.operations]

    if operation_types and operation_types.count(operation_types[0]) == len(operation_types):
      self.operation_weights[operation_types[0]] -= base_adjustment

    # Normalize weights
    total = sum(self.operation_weights.values())

    for op_type in self.operation_weights:
      self.operation_weights[op_type] /= total


if __name__ == '__main__':
  schema = Schema.from_file('../../examples/data_structure_tpch_csv.json')

  # schema_data = {
  #   'entities': {
  #     'customer': {
  #       'properties': {
  #         'id': {'type': 'int', 'min': 1, 'max': 1000},
  #         'name': {'type': 'string', 'starting_character': ['A', 'B', 'C']},
  #         'age': {'type': 'int', 'min': 18, 'max': 100},
  #       },
  #       'primary_key': 'id',
  #       'foreign_keys': {},
  #     },
  #     'order': {
  #       'properties': {
  #         'id': {'type': 'int', 'min': 1, 'max': 10000},
  #         'customer_id': {'type': 'int', 'min': 1, 'max': 1000},
  #         'total': {'type': 'float', 'min': 0, 'max': 1000},
  #       },
  #       'primary_key': 'id',
  #       'foreign_keys': {'customer_id': ['id', 'customer']},
  #     },
  #   }
  # }

  # schema = Schema(
  #   entities={
  #     name: Entity.from_configuration(config) for name, config in schema_data['entities'].items()
  #   }
  # )

  query_structure = QueryStructure(
    allow_aggregation=True,
    allow_group_by=True,
    allow_projection=True,
    multi_line=False,  # TODO: Handle the multi-line case
    num_merges=2,
    num_queries=5,
    num_selections=3,
  )

  generator = Generator(schema, query_structure)

  for i in range(25):
    query = generator.generate()

    if query:
      print(f'Query {i + 1}:')

      print(str(query))

      print('\nOperations:')

      for op in query.operations:
        print(f'  {type(op).__name__}: {op}')

      print('\nAvailable columns:')

      for entity, columns in query.available_columns.items():
        print(f"  {entity}: {', '.join(columns)}")

      print('\n' + '=' * 100 + '\n')

  print('\nFinal operation weights:')

  for op_type, weight in generator.operation_weights.items():
    print(f'  {op_type.__name__}: {weight:.2f}')
