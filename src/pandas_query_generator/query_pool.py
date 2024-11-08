import multiprocessing as mp
import os
import typing as t
from collections import Counter
from dataclasses import dataclass, field
from functools import partial

import pandas as pd
from tqdm import tqdm

from pandas_query_generator.arguments import QueryFilter

from .group_by_aggregation import GroupByAggregation
from .merge import Merge
from .projection import Projection
from .query import Query
from .selection import Selection

QueryResult = t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]


@dataclass
class ExecutionStatistics:
  """Statistics about query execution results"""

  successful_executions: int = 0
  failed_executions: int = 0
  non_empty_results: int = 0
  empty_results: int = 0
  success_rate: float = 0.0
  non_empty_rate: float = 0.0
  errors: Counter[str] = field(default_factory=Counter)


@dataclass
class QueryStatistics:
  """Comprehensive statistics about queries and their execution"""

  total_queries: int = 0
  operations: t.Dict[str, int] = field(default_factory=dict)
  merges: Counter[int] = field(default_factory=Counter)
  selections: Counter[int] = field(default_factory=Counter)
  projections: Counter[int] = field(default_factory=Counter)
  groupby_aggregations: Counter[int] = field(default_factory=Counter)
  entities_used: Counter[str] = field(default_factory=Counter)
  avg_operations_per_query: float = 0.0
  avg_merge_count: float = 0.0
  avg_selection_conditions: float = 0.0
  avg_projection_columns: float = 0.0
  avg_groupby_columns: float = 0.0
  max_merge_depth: int = 0
  max_merge_chain: int = 0
  execution_results: ExecutionStatistics = field(default_factory=ExecutionStatistics)


@dataclass
class QueryPool:
  """
  A pool of database queries with methods for execution, filtering, and analysis.

  This class manages a collection of Query objects and provides functionality for:
  - Parallel query execution against sample data
  - Filtering queries based on execution results
  - Generating and displaying query statistics
  - Saving queries to files

  The class maintains both the queries and their execution results (if any) to avoid
  redundant executions when performing multiple operations.

  Attributes:
    queries (List[Query]): List of Query objects in the pool
    _results (List[QueryResult]): Cached execution results for the queries
        Each result is a tuple of (Optional[DataFrame/Series], Optional[str])
        representing (result, error_message)
    _pool: Optional process pool to reuse
  """

  queries: t.List[Query]
  _results: t.List[QueryResult] = field(default_factory=list)

  def __len__(self) -> int:
    """Return the number of queries in the pool."""
    return len(self.queries)

  def __iter__(self) -> t.Iterator[Query]:
    """Iterate over the queries in the pool."""
    return iter(self.queries)

  def _execute_multi_line_query(
    self, query: Query, sample_data: t.Dict[str, pd.DataFrame]
  ) -> QueryResult:
    """Execute a multi-line query by executing each line sequentially."""
    try:
      local_vars = sample_data.copy()
      for line in str(query).split('\n'):
        df_name, expression = line.split(' = ', 1)
        result = eval(expression, {}, local_vars)
        local_vars[df_name] = result
      last_df = max(k for k in local_vars.keys() if k.startswith('df'))
      return local_vars[last_df], None
    except Exception as e:
      return None, f'{type(e).__name__}: {str(e)}'

  def _execute_single_query(
    self, query: Query, sample_data: t.Dict[str, pd.DataFrame]
  ) -> QueryResult:
    """Execute a single query and handle any errors."""
    try:
      if query.multi_line:
        return self._execute_multi_line_query(query, sample_data)
      result = pd.eval(str(query), local_dict=sample_data)
      if isinstance(result, (pd.DataFrame, pd.Series)):
        return result, None
      return None, f'Result was not a DataFrame or Series: {type(result)}'
    except Exception as e:
      return None, f'{type(e).__name__}: {str(e)}'

  def execute(
    self,
    sample_data: t.Dict[str, pd.DataFrame],
    with_status: bool = False,
    force_execute: bool = False,
    num_processes: t.Optional[int] = None,
  ) -> t.List[QueryResult]:
    """
    Execute all queries in parallel against the provided sample data.

    Args:
      sample_data: Dictionary mapping entity names to their sample DataFrames
      with_status: If True, displays a progress bar during execution
      force_execute: If True, re-executes all queries even if results exist
      num_processes:
        Optional number of processes for parallel execution.
        If None, uses the system's CPU count

    Returns:
      List of QueryResult tuples containing (result, error) for each query
    """
    if len(self.queries) == 0:
      return []

    if len(self._results) > 0 and not force_execute:
      return self._results

    f = partial(self._execute_single_query, sample_data=sample_data)

    ctx = mp.get_context('fork')

    with ctx.Pool(num_processes) as pool:
      iterator = pool.imap(f, self.queries)

      if with_status:
        iterator = tqdm(iterator, total=len(self.queries), desc='Executing queries', unit='query')

      self._results = list(iterator)

    return self._results

  def filter(
    self,
    sample_data: t.Dict[str, pd.DataFrame],
    filter_type: QueryFilter,
    force_execute: bool = False,
    with_status: bool = False,
  ) -> None:
    """
    Filter queries based on their execution results.

    Args:
      sample_data: Dictionary mapping entity names to their sample DataFrames
      filter_type: Type of filter to apply (NON_EMPTY, EMPTY, HAS_ERROR, WITHOUT_ERROR)
      force_execute: If True, re-executes all queries even if results exist
      with_status: If True, displays a progress bar during execution

    This method modifies the query pool in-place, keeping only queries that match
    the filter criteria. If execution results don't exist or force_reexecute is True,
    it executes the queries first.
    """
    if len(self.queries) == 0:
      return

    if not self._results or force_execute:
      self._results = self.execute(sample_data, with_status)

    filtered_queries, filtered_results = [], []

    for query, result_tuple in zip(self.queries, self._results):
      (
        result,
        error,
      ) = result_tuple

      should_keep = False

      match filter_type:
        case QueryFilter.NON_EMPTY:
          should_keep = result is not None and (
            (isinstance(result, pd.DataFrame) and not result.empty)
            or (isinstance(result, pd.Series) and result.size > 0)
          )
        case QueryFilter.EMPTY:
          should_keep = result is not None and (
            (isinstance(result, pd.DataFrame) and result.empty)
            or (isinstance(result, pd.Series) and result.size == 0)
          )
        case QueryFilter.HAS_ERROR:
          should_keep = error is not None
        case QueryFilter.WITHOUT_ERROR:
          should_keep = error is None

      if should_keep:
        filtered_queries.append(query)
        filtered_results.append(result_tuple)

    self.queries, self._results = filtered_queries, filtered_results

  def calculate_statistics(self) -> QueryStatistics:
    """Generate comprehensive statistics about the queries and their execution."""
    statistics = QueryStatistics()
    statistics.total_queries = len(self.queries)

    total_operations = 0

    total_merges = 0
    total_selection_conditions = 0
    total_projection_columns = 0
    total_groupby_columns = 0

    max_merge_depth = max_merge_chain = 0

    for query in self.queries:
      statistics.entities_used[query.entity] += 1

      query_merge_depth = query_merge_chain = current_merge_depth = 0

      for op in query.operations:
        total_operations += 1

        if isinstance(op, Merge):
          total_merges += 1
          query_merge_chain += 1
          current_merge_depth += 1
          statistics.merges[len(op.right.operations)] += 1

          def count_nested_merges(nested_ops):
            nested_depth = 0
            for nested_op in nested_ops:
              if isinstance(nested_op, Merge):
                nested_depth = max(
                  nested_depth, 1 + count_nested_merges(nested_op.right.operations)
                )
            return nested_depth

          query_merge_depth = max(
            query_merge_depth, current_merge_depth + count_nested_merges(op.right.operations)
          )
        elif isinstance(op, Selection):
          total_selection_conditions += len(op.conditions)
          statistics.selections[len(op.conditions)] += 1
        elif isinstance(op, Projection):
          total_projection_columns += len(op.columns)
          statistics.projections[len(op.columns)] += 1
        elif isinstance(op, GroupByAggregation):
          total_groupby_columns += len(op.group_by_columns)
          statistics.groupby_aggregations[len(op.group_by_columns)] += 1

        statistics.operations[type(op).__name__] = (
          statistics.operations.get(type(op).__name__, 0) + 1
        )

      max_merge_depth = max(max_merge_depth, query_merge_depth)
      max_merge_chain = max(max_merge_chain, query_merge_chain)

    if statistics.total_queries > 0:
      statistics.avg_operations_per_query = total_operations / statistics.total_queries

      merge_count = statistics.operations.get('Merge', 0)
      if merge_count > 0:
        statistics.avg_merge_count = total_merges / statistics.total_queries

      selection_count = statistics.operations.get('Selection', 0)
      if selection_count > 0:
        statistics.avg_selection_conditions = total_selection_conditions / selection_count

      projection_count = statistics.operations.get('Projection', 0)
      if projection_count > 0:
        statistics.avg_projection_columns = total_projection_columns / projection_count

      groupby_count = statistics.operations.get('GroupByAggregation', 0)
      if groupby_count > 0:
        statistics.avg_groupby_columns = total_groupby_columns / groupby_count

    statistics.max_merge_depth = max_merge_depth
    statistics.max_merge_chain = max_merge_chain

    if len(self._results) > 0:
      statistics.execution_results = self._calculate_execution_statistics()

    return statistics

  def _calculate_execution_statistics(self) -> ExecutionStatistics:
    """Calculate statistics about query execution results."""
    statistics = ExecutionStatistics()

    for result, error in self._results:
      if error is not None:
        statistics.failed_executions += 1
        statistics.errors[error] += 1
      else:
        statistics.successful_executions += 1
        if isinstance(result, (pd.DataFrame, pd.Series)):
          if (isinstance(result, pd.DataFrame) and not result.empty) or (
            isinstance(result, pd.Series) and result.size > 0
          ):
            statistics.non_empty_results += 1

    total = len(self._results)
    successful = statistics.successful_executions
    statistics.empty_results = total - statistics.non_empty_results

    if total > 0:
      statistics.success_rate = (successful / total) * 100
      statistics.non_empty_rate = (statistics.non_empty_results / total) * 100

    return statistics

  def _format_statistics(self, statistics: QueryStatistics) -> str:
    """Format statistics into a readable string."""
    lines = [
      f'Total queries generated: {statistics.total_queries}',
      f'Average operations per query: {statistics.avg_operations_per_query:.2f}',
      '',
      'Operation Averages:',
      f'  Average merges per query: {statistics.avg_merge_count:.2f}',
      f'  Average conditions per selection: {statistics.avg_selection_conditions:.2f}',
      f'  Average columns per projection: {statistics.avg_projection_columns:.2f}',
      f'  Average columns per group by: {statistics.avg_groupby_columns:.2f}',
      '',
      'Merge Complexity:',
      f'  Maximum merge depth: {statistics.max_merge_depth}',
      f'  Maximum merge chain length: {statistics.max_merge_chain}',
      '',
      'Operation Distribution:',
    ]

    if statistics.operations:
      total_ops = sum(statistics.operations.values())
      for op, count in statistics.operations.items():
        percentage = (count / total_ops) * 100
        lines.append(f'  {op}: {count} ({percentage:.2f}%)')

    if statistics.merges:
      lines.append('\nMerge Operation Details:')
      for complexity, count in sorted(statistics.merges.items()):
        percentage = (count / statistics.operations['Merge']) * 100
        lines.append(f'  {complexity} operations in right query: {count} ({percentage:.2f}%)')

    if statistics.selections:
      lines.append('\nSelection Condition Distribution:')
      for conditions, count in sorted(statistics.selections.items()):
        percentage = (count / statistics.operations['Selection']) * 100
        lines.append(f'  {conditions} conditions: {count} ({percentage:.2f}%)')

    if statistics.projections:
      lines.append('\nProjection Column Distribution:')
      for columns, count in sorted(statistics.projections.items()):
        percentage = (count / statistics.operations['Projection']) * 100
        lines.append(f'  {columns} columns: {count} ({percentage:.2f}%)')

    if statistics.groupby_aggregations:
      lines.append('\nGroup By Column Distribution:')
      for columns, count in sorted(statistics.groupby_aggregations.items()):
        percentage = (count / statistics.operations['GroupByAggregation']) * 100
        lines.append(f'  {columns} columns: {count} ({percentage:.2f}%)')

    lines.extend([''] + self._format_execution_statistics(statistics.execution_results))

    return '\n'.join(lines)

  def _format_execution_statistics(self, statistics: ExecutionStatistics) -> t.List[str]:
    """Format execution statistics into a list of strings."""
    lines = [
      '\nQuery Execution Results:',
      f'  Successful executions: {statistics.successful_executions} '
      f'({statistics.success_rate:.2f}%)',
      f'  Failed executions: {statistics.failed_executions}',
      f'  Queries with non-empty results: {statistics.non_empty_results} '
      f'({statistics.non_empty_rate:.2f}%)',
      f'  Queries with empty results: {statistics.empty_results}',
    ]

    if statistics.errors:
      lines.append('\nError distribution:')
      total_errors = sum(statistics.errors.values())
      for error, count in statistics.errors.most_common():
        percentage = (count / total_errors) * 100
        lines.append(f'  {count} ({percentage:.2f}%) - {error}')

    return lines

  def print_statistics(
    self,
    sample_data: t.Dict[str, pd.DataFrame],
    force_execute: bool = False,
    with_status: bool = False,
  ) -> None:
    """
    Generate and print detailed statistics about the queries and their execution.

    Args:
      sample_data: Dictionary mapping entity names to their sample DataFrames
      force_execute: If True, re-executes all queries even if results exist
      with_status: If True, displays a progress bar during execution
    """
    if len(self.queries) == 0:
      return

    if not self._results or force_execute:
      self._results = self.execute(sample_data, with_status)

    statistics = self.calculate_statistics()

    for i, ((result, error), query) in enumerate(zip(self._results, self.queries), 1):
      print(f'Query {i}:\n')
      print(str(query) + '\n')

      if result is not None:
        print('Results:\n')
        print(result)
      elif error is not None:
        print('Error:\n')
        print(error)

      print()

    print(self._format_statistics(statistics))

  def save(self, output_file: str, create_dirs: bool = True) -> None:
    """
    Save all queries to a file, one query per line.

    Args:
      output_file: Path to the output file
      create_dirs: If True, creates parent directories if they don't exist

    The queries are saved in their string representation, with empty queries
    filtered out and whitespace trimmed.
    """
    if create_dirs and os.path.dirname(output_file):
      os.makedirs(os.path.dirname(output_file), exist_ok=True)

    queries = filter(None, map(lambda q: str(q).strip(), self.queries))

    with open(output_file, 'w+') as f:
      f.write('\n\n'.join(queries))

  def sort(self) -> None:
    """
    Sort queries by their complexity and update results accordingly.

    The sorting is stable and maintains the association between queries
    and their execution results (if any exist).

    Duplicate queries are removed, keeping the one with a successful result if available.
    """
    if not self._results:
      unique_queries = {}

      for query in self.queries:
        key = (str(query), query.complexity)
        if key not in unique_queries:
          unique_queries[key] = query

      self.queries = sorted(unique_queries.values())
    else:
      unique_queries = {}

      for query, (result, error) in zip(self.queries, self._results):
        key = (str(query), query.complexity)

        existing = unique_queries.get(key)

        if (not existing) or (error is None and existing[1][1] is not None):
          unique_queries[key] = (query, (result, error))

      if unique_queries:
        sorted_pairs = sorted(unique_queries.values(), key=lambda x: x[0])
        self.queries, self._results = map(list, zip(*sorted_pairs))
      else:
        self.queries, self._results = [], []
