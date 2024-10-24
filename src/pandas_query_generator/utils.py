import typing as t
from collections import Counter

import pandas as pd

from .group_by_aggregation import GroupByAggregation
from .merge import Merge
from .projection import Projection
from .query import Query
from .selection import Selection


class ExecutionResults(t.TypedDict):
  """Statistics about query execution results"""

  successful_executions: int
  failed_executions: int
  non_empty_results: int
  empty_results: int
  success_rate: float
  non_empty_rate: float
  errors: Counter[str]  # Error message -> count


class OperationStats(t.TypedDict):
  """Statistics for each operation type"""

  total: int
  complexity_distribution: Counter[int]  # Complexity level -> count


class QueryStats(t.TypedDict):
  """Comprehensive statistics about queries and their execution"""

  total_queries: int
  operations: t.Dict[str, int]  # Operation name -> count
  merges: Counter[int]  # Number of operations in right query -> count
  selections: Counter[int]  # Number of conditions -> count
  projections: Counter[int]  # Number of columns -> count
  groupby_aggregations: Counter[int]  # Number of groupby columns -> count
  entities_used: Counter[str]  # Entity name -> count
  avg_operations_per_query: float
  execution_results: ExecutionResults  # Execution statistics and errors


def execute_query(
  query: Query, sample_data: t.Dict[str, pd.DataFrame]
) -> t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]:
  """
  Execute a given query on the provided sample data and capture any errors.

  Args:
    query (Query): The Query object to be executed
    sample_data (Dict[str, DataFrame]): Dictionary of sample data for each entity

  Returns:
    Tuple[Optional[Union[DataFrame, Series]], Optional[str]]:
      - The result of the query execution if successful, None if failed
      - The error message if execution failed, None if successful
  """
  try:
    full_query = str(query)
    environment = {**sample_data}
    exec(full_query, globals(), environment)
    result = environment.get(query.entity)

    if isinstance(result, (pd.DataFrame, pd.Series)):
      return result, None
    return None, f'Result was not a DataFrame or Series: {type(result)}'
  except Exception as e:
    return None, f'{type(e).__name__}: {str(e)}'


def generate_query_statistics(
  queries: t.List[Query],
  results: t.Optional[
    t.List[t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]]
  ] = None,
) -> QueryStats:
  """
  Generate comprehensive statistics about queries and their execution results.

  Args:
    queries: List of Query objects to analyze
    results: Optional list of tuples containing (execution_result, error_message)

  Returns:
    QueryStats containing detailed statistics
  """
  stats: QueryStats = {
    'total_queries': len(queries),
    'operations': Counter(),
    'merges': Counter(),
    'selections': Counter(),
    'projections': Counter(),
    'groupby_aggregations': Counter(),
    'entities_used': Counter(),
    'avg_operations_per_query': 0.0,
    'execution_results': {
      'successful_executions': 0,
      'failed_executions': 0,
      'non_empty_results': 0,
      'empty_results': 0,
      'success_rate': 0.0,
      'non_empty_rate': 0.0,
      'errors': Counter(),  # Track frequency of different error types
    },
  }

  total_operations = 0

  for query in queries:
    stats['entities_used'][query.entity] += 1

    for op in query.operations:
      total_operations += 1
      if isinstance(op, Merge):
        stats['merges'][len(op.right.operations)] += 1
      elif isinstance(op, Selection):
        stats['selections'][len(op.conditions)] += 1
      elif isinstance(op, Projection):
        stats['projections'][len(op.columns)] += 1
      elif isinstance(op, GroupByAggregation):
        stats['groupby_aggregations'][len(op.group_by_columns)] += 1
      stats['operations'][type(op).__name__] += 1

  if queries:
    stats['avg_operations_per_query'] = total_operations / len(queries)

  if results is not None:
    for result, error in results:
      if result is None:
        stats['execution_results']['failed_executions'] += 1
        if error:
          stats['execution_results']['errors'][error] += 1
      else:
        stats['execution_results']['successful_executions'] += 1
        if isinstance(result, (pd.DataFrame, pd.Series)):
          if (isinstance(result, pd.DataFrame) and not result.empty) or (
            isinstance(result, pd.Series) and result.size > 0
          ):
            stats['execution_results']['non_empty_results'] += 1

    total = stats['total_queries']
    successful = stats['execution_results']['successful_executions']
    non_empty = stats['execution_results']['non_empty_results']

    stats['execution_results']['empty_results'] = total - non_empty

    if total > 0:
      stats['execution_results']['success_rate'] = (successful / total) * 100
      stats['execution_results']['non_empty_rate'] = (non_empty / total) * 100

  return stats


def print_statistics(stats: QueryStats) -> None:
  """Print comprehensive statistics about queries and their execution."""
  print(f"Total queries generated: {stats['total_queries']}")
  print(f"Average operations per query: {stats['avg_operations_per_query']:.2f}")

  print('\nOperation distribution:')
  for op, count in stats['operations'].items():
    percentage = (count / stats['total_queries']) * 100
    print(f'  {op}: {count} ({percentage:.2f}%)')

  print('\nMerge complexity (number of operations in right query):')
  if stats['merges']:
    for complexity, count in sorted(stats['merges'].items()):
      percentage = (count / stats['operations']['Merge']) * 100
      print(f'  {complexity} operations: {count} ({percentage:.2f}%)')

  print('\nSelection complexity (number of conditions):')
  if stats['selections']:
    for conditions, count in sorted(stats['selections'].items()):
      percentage = (count / stats['operations']['Selection']) * 100
      print(f'  {conditions} conditions: {count} ({percentage:.2f}%)')

  print('\nProjection complexity (number of columns):')
  if stats['projections']:
    for columns, count in sorted(stats['projections'].items()):
      percentage = (count / stats['operations']['Projection']) * 100
      print(f'  {columns} columns: {count} ({percentage:.2f}%)')

  print('\nGroupBy Aggregation complexity (number of groupby columns):')
  if stats['groupby_aggregations']:
    for columns, count in sorted(stats['groupby_aggregations'].items()):
      percentage = (count / stats['operations']['GroupByAggregation']) * 100
      print(f'  {columns} columns: {count} ({percentage:.2f}%)')

  print('\nEntity usage:')
  for entity, count in stats['entities_used'].items():
    percentage = (count / stats['total_queries']) * 100
    print(f'  {entity}: {count} ({percentage:.2f}%)')

  if stats['execution_results'].get('successful_executions', 0) > 0:
    print('\nQuery Execution Results:')
    print(
      f"  Successful executions: {stats['execution_results']['successful_executions']} "
      f"({stats['execution_results']['success_rate']:.2f}%)"
    )
    print(f"  Failed executions: {stats['execution_results']['failed_executions']}")
    print(
      f"  Queries with non-empty results: {stats['execution_results']['non_empty_results']} "
      f"({stats['execution_results']['non_empty_rate']:.2f}%)"
    )
    print(f"  Queries with empty results: {stats['execution_results']['empty_results']}")

  if stats['execution_results']['errors']:
    print('\nError distribution:')
    total_errors = sum(stats['execution_results']['errors'].values())
    for error, count in stats['execution_results']['errors'].most_common():
      percentage = (count / total_errors) * 100
      print(f'  {count} ({percentage:.2f}%) - {error}')
