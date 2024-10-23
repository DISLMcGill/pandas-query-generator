import typing as t
from collections import Counter

import pandas as pd

from .group_by import GroupByAggregation
from .merge import Merge
from .projection import Projection
from .query import Query
from .selection import Selection


class OperationStats(t.TypedDict):
  """Statistics for each operation type"""

  total: int
  complexity_distribution: Counter


class QueryStats(t.TypedDict):
  """Comprehensive statistics about queries and their execution"""

  total_queries: int
  operations: t.Dict[str, int]  # Operation name -> count
  merges: Counter  # Number of operations in right query -> count
  selections: Counter  # Number of conditions -> count
  projections: Counter  # Number of columns -> count
  groupby_aggregations: Counter  # Number of groupby columns -> count
  entities_used: Counter  # Entity name -> count
  avg_operations_per_query: float
  execution_results: t.Dict[str, t.Union[int, float]]  # Result statistics


def execute_query(
  query: Query, sample_data: t.Dict[str, pd.DataFrame]
) -> t.Optional[t.Union[pd.DataFrame, pd.Series]]:
  """
  Execute a given query on the provided sample data.

  This function attempts to execute the query against the sample data and returns
  the result. If an exception occurs during execution, it returns None.

  Args:
    query (Query):
      The Query object to be executed. This should be a valid
      Query instance containing the entity and operations to perform.

    sample_data (Dict[str, DataFrame]):
      A dictionary containing sample data for each
      entity in the schema. The keys should be entity
      names, and the values should be the corresponding
      sample data as pandas DataFrames.

  Returns:
    Optional[Union[DataFrame, Series]]:
      The result of the query execution if successful,
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


def generate_query_statistics(
  queries: t.List[Query],
  results: t.Optional[t.List[t.Optional[t.Union[pd.DataFrame, pd.Series]]]] = None,
) -> QueryStats:
  """
  Generate comprehensive statistics about queries and their execution results.

  Args:
      queries: List of Query objects to analyze
      results: Optional list of query execution results

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
    for result in results:
      if result is None:
        stats['execution_results']['failed_executions'] += 1
      else:
        stats['execution_results']['successful_executions'] += 1

        if isinstance(result, (pd.DataFrame, pd.Series)):
          if (isinstance(result, pd.DataFrame) and not result.empty) or (
            isinstance(result, pd.Series) and result.size > 0
          ):
            stats['execution_results']['non_empty_results'] += 1
          else:
            stats['execution_results']['empty_results'] += 1

    total = stats['total_queries']

    if total > 0:
      stats['execution_results']['success_rate'] = (
        stats['execution_results']['successful_executions'] / total
      ) * 100
      stats['execution_results']['non_empty_rate'] = (
        stats['execution_results']['non_empty_results'] / total
      ) * 100

  return stats


def print_statistics(stats: QueryStats) -> None:
  """
  Print comprehensive statistics about queries and their execution.

  Args:
      stats: QueryStats containing the statistics to print
  """
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
      f"Successful executions: {stats['execution_results']['successful_executions']} "
      f"({stats['execution_results']['success_rate']:.2f}%)"
    )

    print(f"Failed executions: {stats['execution_results']['failed_executions']}")

    print(
      f"Queries with non-empty results: {stats['execution_results']['non_empty_results']} "
      f"({stats['execution_results']['non_empty_rate']:.2f}%)"
    )

    print(f"Queries with empty results: {stats['execution_results']['empty_results']}")
