from __future__ import annotations

import random
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta

from entity import *
from schema import Schema


@dataclass
class QueryStructure:
  max_depth: int
  num_merges: int
  num_selections: int
  allow_projection: bool
  allow_aggregation: bool


@dataclass
class Operation(ABC):
  @abstractmethod
  def to_pandas(self, df_name: str | None = None) -> str:
    pass


@dataclass
class DataFrameOperation(Operation):
  df_name: str
  child_operations: t.List[Operation] = field(default_factory=list)

  def add_operation(self, operation: Operation):
    self.child_operations.append(operation)

  def to_pandas(self, df_name: str | None = None) -> str:
    result = df_name or self.df_name
    for op in self.child_operations:
      result = op.to_pandas(result)
    return result


@dataclass
class Selection(Operation):
  conditions: t.List[t.Tuple[str, str, t.Any]]

  def to_pandas(self, df_name: str | None = None) -> str:
    conditions = []

    for col, op, val in self.conditions:
      if op.startswith('.'):
        # Handle string operations
        str_method = op.split('.', 1)[1]
        condition = f"({df_name}['{col}'].{str_method}({repr(val)}))"
      else:
        # Handle regular comparisons
        condition = f"({df_name}['{col}'] {op} {repr(val)})"
      conditions.append(condition)

    return f"{df_name}[{' | '.join(conditions)}]"


@dataclass
class Projection(Operation):
  columns: t.List[str]

  def to_pandas(self, df_name: str | None = None) -> str:
    columns = ', '.join(f"'{col}'" for col in self.columns)
    return f'{df_name}[[{columns}]]'


@dataclass
class Merge(Operation):
  right_df: DataFrameOperation
  left_on: str
  right_on: str

  def to_pandas(self, df_name: str | None = None) -> str:
    right_df = self.right_df.to_pandas()
    return f"{df_name}.merge({right_df}, left_on='{self.left_on}', right_on='{self.right_on}')"


@dataclass
class GroupByAggregate(Operation):
  group_columns: t.List[str]
  agg_function: str
  options: t.Dict[str, t.Any] = field(default_factory=dict)

  def to_pandas(self, df_name: str | None = None) -> str:
    group_cols = ', '.join(f"'{col}'" for col in self.group_columns)
    options_str = ', '.join(f'{k}={v}' for k, v in self.options.items())
    return f"{df_name}.groupby(by=[{group_cols}]).agg('{self.agg_function}', {options_str})"


@dataclass
class Query:
  root_operation: DataFrameOperation

  def to_pandas(self) -> str:
    return self.root_operation.to_pandas()


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema = schema
    self.query_structure = query_structure
    self.data_ranges = self._extract_data_ranges()
    self.entities_used = set()

  def _extract_data_ranges(self):
    data_ranges = {}
    for entity_name, entity in self.schema.entities.items():
      data_ranges[entity_name] = {}
      for prop_name, prop in entity.properties.items():
        if isinstance(prop, (PropertyInt, PropertyFloat, PropertyDate)):
          data_ranges[entity_name][prop_name] = (prop.min, prop.max)
    return data_ranges

  def generate(self) -> Query:
    root_df = random.choice(list(self.schema.entities.keys()))
    self.entities_used.add(root_df)
    root_operation = DataFrameOperation(root_df)
    self._build_query_tree(root_operation, depth=0)
    return Query(root_operation)

  def _build_query_tree(self, current_operation: DataFrameOperation, depth: int):
    if depth > self.query_structure.max_depth:
      return

    operations = self._choose_operations(depth)

    for op_type in operations:
      if op_type == Selection:
        self._add_selection(current_operation)
      elif op_type == Projection:
        self._add_projection(current_operation)
      elif op_type == Merge:
        self._add_merge(current_operation, depth)
      elif op_type == GroupByAggregate:
        self._add_group_by_aggregate(current_operation)

  def _choose_operations(self, depth: int) -> t.List[t.Type[Operation]]:
    operations = []
    if depth < self.query_structure.max_depth and len(self.entities_used) < len(
      self.schema.entities
    ):
      operations.append(Merge)
    if random.random() < 0.7:  # 70% chance to add a selection
      operations.append(Selection)
    if (
      self.query_structure.allow_projection and random.random() < 0.5
    ):  # 50% chance to add a projection
      operations.append(Projection)
    if depth == self.query_structure.max_depth and self.query_structure.allow_aggregation:
      operations.append(GroupByAggregate)
    random.shuffle(operations)
    return operations

  def _add_selection(self, current_operation: DataFrameOperation):
    conditions = self._generate_conditions(current_operation.df_name)
    current_operation.add_operation(Selection(conditions))

  def _add_projection(self, current_operation: DataFrameOperation):
    columns = self._choose_columns(current_operation.df_name)
    current_operation.add_operation(Projection(columns))

  def _add_merge(self, current_operation: DataFrameOperation, depth: int):
    right_df = self._choose_merge_target(current_operation.df_name)
    right_operation = DataFrameOperation(right_df)
    self._build_query_tree(right_operation, depth + 1)
    left_on, right_on = self._choose_merge_columns(current_operation.df_name, right_df)
    current_operation.add_operation(Merge(right_operation, left_on, right_on))

  def _add_group_by_aggregate(self, current_operation: DataFrameOperation):
    group_columns = self._choose_group_columns(current_operation.df_name)
    agg_function = random.choice(['mean', 'sum', 'count', 'min', 'max'])
    options = {'numeric_only': True} if agg_function in ['mean', 'sum'] else {}
    current_operation.add_operation(GroupByAggregate(group_columns, agg_function, options))

  def _generate_conditions(self, df_name: str) -> t.List[t.Tuple[str, str, t.Any]]:
    num_conditions = random.randint(1, 3)
    conditions = []
    for _ in range(num_conditions):
      column = random.choice(list(self.schema.entities[df_name].properties.keys()))
      property = self.schema.entities[df_name].properties[column]
      operator, value = self._generate_condition(property)
      conditions.append((column, operator, value))
    return conditions

  def _generate_condition(self, property: Property) -> t.Tuple[str, t.Any]:
    operators = {
      PropertyInt: ['>', '<', '>=', '<=', '==', '!='],
      PropertyFloat: ['>', '<', '>=', '<='],
      PropertyEnum: ['==', '!=', '.isin'],
      PropertyString: ['==', '!=', '.str.startswith', '.str.contains'],
      PropertyDate: ['>', '<', '>=', '<=', '==', '!='],
    }

    if isinstance(property, PropertyInt):
      operator = random.choice(operators[PropertyInt])
      value = random.randint(property.min, property.max)
    elif isinstance(property, PropertyFloat):
      operator = random.choice(operators[PropertyFloat])
      value = round(random.uniform(property.min, property.max), 2)
    elif isinstance(property, PropertyEnum):
      operator = random.choice(operators[PropertyEnum])
      if operator == '.isin':
        value = random.sample(property.values, k=random.randint(1, len(property.values)))
      else:
        value = random.choice(property.values)
    elif isinstance(property, PropertyString):
      operator = random.choice(operators[PropertyString])
      if operator in ['.str.startswith', '.str.contains']:
        value = random.choice(property.starting_character)
      else:
        value = ''.join(
          random.choices(''.join(property.starting_character) + 'abcdefghijklmnopqrstuvwxyz', k=6)
        )
    elif isinstance(property, PropertyDate):
      operator = random.choice(operators[PropertyDate])
      days_between = (property.max - property.min).days
      random_days = random.randint(0, days_between)
      value = (property.min + timedelta(days=random_days)).strftime('%Y-%m-%d')

    return operator, value

  def _choose_columns(self, df_name: str) -> t.List[str]:
    all_columns = list(self.schema.entities[df_name].properties.keys())
    num_columns = random.randint(1, len(all_columns))
    return random.sample(all_columns, num_columns)

  def _choose_merge_target(self, _: str) -> str:
    available_entities = set(self.schema.entities.keys()) - self.entities_used
    if not available_entities:
      return random.choice(list(self.schema.entities.keys()))
    target_df = random.choice(list(available_entities))
    self.entities_used.add(target_df)
    return target_df

  def _choose_merge_columns(self, left_df: str, right_df: str) -> t.Tuple[str, str]:
    left_columns = set(self.schema.entities[left_df].properties.keys())
    right_columns = set(self.schema.entities[right_df].properties.keys())

    # First, try to find a foreign key relationship
    for left_col, (ref_entity, ref_col) in self.schema.entities[left_df].foreign_keys.items():
      if ref_entity == right_df and ref_col in right_columns:
        return left_col, ref_col

    # If no foreign key, look for common column names
    common_columns = left_columns.intersection(right_columns)
    if common_columns:
      column = random.choice(list(common_columns))
      return column, column

    # If no common columns, choose random columns
    return random.choice(list(left_columns)), random.choice(list(right_columns))

  def _choose_group_columns(self, df_name: str) -> t.List[str]:
    all_columns = list(self.schema.entities[df_name].properties.keys())
    num_group_columns = random.randint(1, min(3, len(all_columns)))
    return random.sample(all_columns, num_group_columns)


# Usage example
if __name__ == '__main__':
  schema = Schema.from_file('../../examples/data_structure_tpch_csv.json')

  query_structure = QueryStructure(
    max_depth=3, num_merges=2, num_selections=2, allow_projection=True, allow_aggregation=True
  )

  generator = Generator(schema, query_structure)

  for _ in range(5):  # Generate 5 queries
    query = generator.generate()
    pandas_query = query.to_pandas()
    print(pandas_query)
    print('=' * 80)
