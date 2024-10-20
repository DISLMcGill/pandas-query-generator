import multiprocessing
import random
import time
import typing as t
from abc import abstractmethod
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial

import pandas as pd
from entity import *
from schema import Schema
from tqdm import tqdm


@dataclass
class QueryStructure:
  """
  Defines the structure and constraints for query generation.
  """

  allow_groupby_aggregation: bool
  max_groupby_columns: int
  max_merges: int
  max_projection_columns: int
  max_projections: int
  max_selection_conditions: int
  max_selections: int
  multi_line: bool


@t.runtime_checkable
class Operation(t.Protocol):
  """
  Abstract base class for query operations.
  """

  @abstractmethod
  def apply(self, entity: str) -> str:
    """
    Apply the operation to the given entity.

    Args:
      entity (str): The name of the entity to apply the operation to.

    Returns:
      str: The string representation of the applied operation.
    """
    ...


@dataclass
class Selection(Operation):
  """
  Represents a selection operation in a query.

  Attributes:
  conditions (List[Tuple[str, str, Any, str]]): List of selection conditions and operators.
    Each tuple contains (column, operation, value, next_condition_operator).
    The last tuple's next_condition_operator is ignored.
  """

  conditions: t.List[t.Tuple[str, str, t.Any, str]] = field(default_factory=list)

  def apply(self, entity: str) -> str:
    if not self.conditions:
      return ''

    formatted_conditions = []

    for i, (col, op, val, next_op) in enumerate(self.conditions):
      if op in ['.str.startswith', '.isin']:
        condition = f'({entity}[{col}]{op}({val}))'
      else:
        condition = f'({entity}[{col}] {op} {val})'

      if i < len(self.conditions) - 1:
        condition += f' {next_op} '

      formatted_conditions.append(f'{condition}')

    return f"[{''.join(formatted_conditions)}]"


@dataclass
class Projection(Operation):
  """
  Represents a projection operation in a query.

  Attributes:
    columns (List[str]): List of column names to project.
  """

  columns: t.List[str] = field(default_factory=list)

  def apply(self, entity: str) -> str:
    return f"[[{', '.join(repr(col) for col in self.columns)}]]"


@dataclass
class Merge(Operation):
  right: 'Query'
  left_on: str
  right_on: str

  def apply(self, entity: str) -> str:
    return f".merge({self.right}, left_on='{self.left_on}', right_on='{self.right_on}')"


@dataclass
class GroupByAggregation(Operation):
  group_by_columns: t.List[str]
  agg_function: str

  def apply(self, entity: str) -> str:
    group_cols = ', '.join(f"'{col}'" for col in self.group_by_columns)
    numeric_only = 'numeric_only=True' if self.agg_function != 'count' else ''
    return f".groupby(by=[{group_cols}]).agg('{self.agg_function}'{f", {numeric_only}" if numeric_only else ""})"


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


class QueryBuilder:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema: Schema = schema
    self.query_structure: QueryStructure = query_structure

    self.operations: t.List[Operation] = []

    self.entity_name = random.choice(list(self.schema.entities.keys()))
    self.entity = self.schema.entities[self.entity_name]

    self.available_columns = list(self.entity.properties.keys())

  def build(self) -> Query:
    """
    Build a query based on the schema and query structure.

    This method orchestrates the query building process. It determines the number
    and types of operations to include in the query, then generates and adds these
    operations to create a complete query.

    Returns:
      Query: The generated query, consisting of an entity and a list of operations.
    """
    query_description: t.Dict[t.Type[Operation], int] = {
      Selection: random.randint(0, self.query_structure.max_selections),
      Projection: random.randint(0, self.query_structure.max_projections),
      Merge: random.randint(0, self.query_structure.max_merges),
    }

    operations: t.List[t.Type[Operation]] = list(query_description.keys())

    for _ in range(sum(query_description.values())):
      operation_type = random.choice(operations)

      if query_description[operation_type] > 0:
        self._add_operation(self._generate_operation(operation_type))
        query_description[operation_type] -= 1

      if query_description[operation_type] == 0:
        operations.remove(operation_type)

    if self.query_structure.allow_groupby_aggregation:
      self._add_operation(self._generate_operation(GroupByAggregation))

    query = Query(self.entity_name, self.operations, self.query_structure.multi_line)

    return query

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
      max_groupby_columns=2,
      max_merges=1,  # Prevent nested merges for simplicity
      max_projection_columns=4,
      max_projections=1,  # Ensure at least one projection for the right side
      max_selection_conditions=2,
      max_selections=1,
      multi_line=False,
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

    right_builder = QueryBuilder(self.schema, right_query_structure)

    right_builder.entity_name = right_entity_name
    right_builder.entity = self.schema.entities[right_entity_name]
    right_builder.available_columns = list(right_builder.entity.properties.keys())

    right_query = right_builder.build()

    return Merge(
      right=Query(right_query.entity, right_query.operations, self.query_structure.multi_line),
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


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema = schema
    self.query_structure = query_structure

  @staticmethod
  def _generate_single_query(schema, query_structure, _):
    return QueryBuilder(schema, query_structure).build()

  def generate(self, queries: int) -> t.List[Query]:
    with multiprocessing.Pool() as pool:
      generate_func = partial(self._generate_single_query, self.schema, self.query_structure)

      return list(
        tqdm(
          pool.imap(generate_func, range(queries)),
          total=queries,
          desc='Generating queries',
          unit='query',
        )
      )


def analyze_queries(queries: t.List[Query]) -> t.Dict[str, t.Any]:
  stats = {
    'total_queries': len(queries),
    'operations': Counter(),
    'merges': Counter(),
    'selections': Counter(),
    'projections': Counter(),
    'groupby_aggregations': Counter(),
    'entities_used': Counter(),
    'avg_operations_per_query': 0,
  }

  for query in queries:
    stats['entities_used'][query.entity] += 1
    operation_count = 0
    for op in query.operations:
      operation_count += 1
      if isinstance(op, Merge):
        stats['merges'][len(op.right.operations)] += 1
      elif isinstance(op, Selection):
        stats['selections'][len(op.conditions)] += 1
      elif isinstance(op, Projection):
        stats['projections'][len(op.columns)] += 1
      elif isinstance(op, GroupByAggregation):
        stats['groupby_aggregations'][len(op.group_by_columns)] += 1
      stats['operations'][type(op).__name__] += 1

    stats['avg_operations_per_query'] += operation_count

  stats['avg_operations_per_query'] /= len(queries)

  return stats


def print_stats(stats: t.Dict[str, t.Any]):
  print(f"Total queries generated: {stats['total_queries']}")
  print(f"Average operations per query: {stats['avg_operations_per_query']:.2f}")
  print('\nOperation distribution:')
  for op, count in stats['operations'].items():
    percentage = (count / stats['total_queries']) * 100
    print(f'  {op}: {count} ({percentage:.2f}%)')

  print('\nMerge complexity (number of operations in right query):')
  for complexity, count in sorted(stats['merges'].items()):
    percentage = (count / stats['operations']['Merge']) * 100
    print(f'  {complexity} operations: {count} ({percentage:.2f}%)')

  print('\nSelection complexity (number of conditions):')
  for conditions, count in sorted(stats['selections'].items()):
    percentage = (count / stats['operations']['Selection']) * 100
    print(f'  {conditions} conditions: {count} ({percentage:.2f}%)')

  print('\nProjection complexity (number of columns):')
  for columns, count in sorted(stats['projections'].items()):
    percentage = (count / stats['operations']['Projection']) * 100
    print(f'  {columns} columns: {count} ({percentage:.2f}%)')

  print('\nGroupBy Aggregation complexity (number of groupby columns):')
  for columns, count in sorted(stats['groupby_aggregations'].items()):
    percentage = (count / stats['operations']['GroupByAggregation']) * 100
    print(f'  {columns} columns: {count} ({percentage:.2f}%)')

  print('\nEntity usage:')
  for entity, count in stats['entities_used'].items():
    percentage = (count / stats['total_queries']) * 100
    print(f'  {entity}: {count} ({percentage:.2f}%)')


def execute_query(
  query: Query, sample_data: t.Dict[str, pd.DataFrame]
) -> t.Optional[t.Union[pd.DataFrame, pd.Series]]:
  """
  Execute a given query on the provided sample data.

  This function attempts to execute the query against the sample data and returns
  the result. If an exception occurs during execution, it returns None.

  Args:
    query (Query): The Query object to be executed. This should be a valid
                   Query instance containing the entity and operations to perform.
    sample_data (Dict[str, DataFrame]): A dictionary containing sample data for each
                                        entity in the schema. The keys should be entity
                                        names, and the values should be the corresponding
                                        sample data as pandas DataFrames.

  Returns:
    Optional[Union[DataFrame, Series]]: The result of the query execution if successful,
                                        which is typically a pandas DataFrame or Series.
                                        Returns None if an exception occurs during
                                        query execution.

  Raises:
    No exceptions are raised by this function. All exceptions during query
    execution are caught and result in a None return value.

  Note:
    This function uses the `exec` built-in function to execute the query string.
    Make sure the Query objects and sample_data are from trusted sources to
    prevent potential security risks associated with executing arbitrary code.
  """
  try:
    full_query, environment = str(query), {**sample_data}
    exec(full_query, globals(), environment)
    result = environment.get(query.entity)
    if isinstance(result, (pd.DataFrame, pd.Series)):
      return result
    return None
  except:
    return None


@contextmanager
def timer(description):
  start = time.time()
  yield
  elapsed_time = time.time() - start
  print(f'Time taken for {description}: {elapsed_time:.2f} seconds')


def execute_query_wrapper(args):
  query, sample_data = args
  return execute_query(query, sample_data)


if __name__ == '__main__':
  schema = Schema.from_file('../../examples/data_structure_tpch_csv.json')

  sample_data = {entity: schema.entities[entity].generate_dataframe() for entity in schema.entities}

  # Users will be able to configure these via the CLI.
  query_structure = QueryStructure(
    allow_groupby_aggregation=True,
    max_groupby_columns=2,
    max_merges=3,
    max_projection_columns=4,
    max_projections=5,
    max_selection_conditions=4,
    max_selections=5,
    multi_line=True,
  )

  generator = Generator(schema, query_structure)

  with timer('Generating and executing 100 queries'):
    queries = generator.generate(100)

    ctx = multiprocessing.get_context('fork')

    with ctx.Pool() as pool:
      results = list(
        tqdm(
          pool.imap(execute_query_wrapper, ((query, sample_data) for query in queries)),
          total=len(queries),
          desc='Executing queries',
          unit='query',
        )
      )

    for i, (query, result) in enumerate(zip(queries, results)):
      print(f'Query {i + 1}')
      print()
      print(query)
      print()
      print('Results:')
      print()
      print(result)

  print_stats(analyze_queries(queries))
