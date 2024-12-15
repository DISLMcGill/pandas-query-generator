import multiprocessing as mp
import os
import statistics as stats
import typing as t
from collections import Counter
from dataclasses import dataclass, field
from functools import partial

import pandas as pd
from tqdm import tqdm

from .arguments import QueryFilter
from .group_by_aggregation import GroupByAggregation
from .merge import Merge
from .projection import Projection
from .query import Query
from .query_structure import QueryStructure
from .selection import Selection

QueryResult = t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]


@dataclass
class ExecutionStatistics:
  """
  Statistics about query execution results.

  This class tracks success/failure rates and categorizes execution outcomes
  to provide insights into query generation quality.

  Attributes:
    successful (int): Number of queries that executed without error
    failed (int): Number of queries that raised an error
    non_empty (int): Number of queries returning data (rows/values)
    empty (int): Number of queries returning empty results
    errors (Counter[str]): Count of each error type encountered

  Example:
    stats = ExecutionStatistics()
    stats.successful = 95
    stats.failed = 5
    stats.errors["KeyError"] = 3
    print(stats)  # Shows execution summary with percentages
  """

  successful: int = 0
  failed: int = 0
  non_empty: int = 0
  empty: int = 0
  errors: Counter[str] = field(default_factory=Counter)

  def __str__(self) -> str:
    total = self.successful + self.failed

    if total == 0:
      return ''

    success_rate, empty_rate = (
      (self.successful / total) * 100,
      (self.empty / total) * 100 if total > 0 else 0,
    )

    lines = [
      f'Execution Results (n = {total}):',
      f'  Success Rate: {success_rate:5.1f}% ({self.successful} / {total})',
      f'  Queries with Empty Result Sets: {empty_rate:4.1f}% ({self.empty} / {total})',
    ]

    if self.errors:
      lines.extend(
        ['', 'Errors:', *[f'  {error}: {count}' for error, count in self.errors.most_common()]]
      )

    return '\n'.join(lines)


@dataclass
class QueryStatistics:
  """
  Statistics comparing actual query characteristics against target parameters.

  Analyzes how closely generated queries match the desired structure parameters
  and collects distributions of various operation characteristics.

  Attributes:
    query_structure: Target parameters for query generation
    total_queries: Total number of queries analyzed
    queries_with_selection: Number of queries containing selection operations
    queries_with_projection: Number of queries containing projection operations
    queries_with_groupby: Number of queries containing groupby operations
    queries_with_merge: Number of queries containing merge operations
    selection_conditions: List of condition counts from each selection operation
    projection_columns: List of column counts from each projection operation
    groupby_columns: List of column counts from each groupby operation
    merge_count: List of merge counts from each query
    execution_results: Statistics about query execution outcomes
  """

  query_structure: QueryStructure
  total_queries: int = 0
  queries_with_selection: int = 0
  queries_with_projection: int = 0
  queries_with_groupby: int = 0
  queries_with_merge: int = 0
  selection_conditions: t.List[int] = field(default_factory=list)
  projection_columns: t.List[int] = field(default_factory=list)
  groupby_columns: t.List[int] = field(default_factory=list)
  merge_count: t.List[int] = field(default_factory=list)
  execution_results: ExecutionStatistics = field(default_factory=ExecutionStatistics)

  @staticmethod
  def _safe_stats(values: t.List[int]) -> tuple[float, float, int]:
    """Calculate mean, standard deviation, and max for a list of values."""
    if not values:
      return 0.0, 0.0, 0
    return (stats.mean(values), stats.stdev(values) if len(values) > 1 else 0.0, max(values))

  @staticmethod
  def _format_frequency(label: str, actual: float, target: t.Optional[float] = None) -> str:
    """Format a frequency line."""
    if target is None:
      return f'  {label} {actual:.1f}%'
    return f'  {label} {actual:.1f}% vs {target*100:.1f}%'

  @staticmethod
  def _format_count(label: str, mean: float, std: float, max_val: int, limit: int) -> str:
    """Format a count line."""
    return f'  {label} {mean:.1f} ± {std:.1f} | {max_val} vs {limit}'

  def __str__(self) -> str:
    if self.total_queries == 0:
      return ''

    probabilities = (
      self.queries_with_selection / self.total_queries * 100,
      self.queries_with_projection / self.total_queries * 100,
      self.queries_with_merge / self.total_queries * 100,
      self.queries_with_groupby / self.total_queries * 100,
    )

    lines = [
      f'Query Statistics (n = {self.total_queries})',
      '',
      'Operation Probabilities (actual vs target):',
      self._format_frequency(
        'Selection:', probabilities[0], self.query_structure.selection_probability
      ),
      self._format_frequency(
        'Projection:', probabilities[1], self.query_structure.projection_probability
      ),
      self._format_frequency(
        'GroupBy:', probabilities[3], self.query_structure.groupby_aggregation_probability
      ),
      self._format_frequency('Merge:', probabilities[2]),
      '',
      'Operation Counts (avg ± std | max vs limit):',
    ]

    for data, label, limit in [
      (
        self.selection_conditions,
        'Selection conditions:',
        self.query_structure.max_selection_conditions,
      ),
      (self.projection_columns, 'Projection columns:', self.query_structure.max_projection_columns),
      (self.groupby_columns, 'GroupBy columns:', self.query_structure.max_groupby_columns),
      (self.merge_count, 'Merges per query:', self.query_structure.max_merges),
    ]:
      if data:
        mean, std, max_val = self._safe_stats(data)
        lines.append(self._format_count(label, mean, std, max_val, limit))

    lines.extend(['', str(self.execution_results)])

    return '\n'.join(lines)


class QueryPool:
  """
  Manages a collection of database queries with execution and analysis capabilities.

  Provides functionality for executing queries in parallel, filtering based on results,
  computing statistics, and managing query persistence. The pool maintains execution
  results to avoid redundant computation when performing multiple operations.

  Attributes:
    _queries: List of Query objects in the pool
    _query_structure: Parameters controlling query generation
    _sample_data: Dictionary mapping entity names to sample DataFrames
    _results: Cached query execution results (DataFrame/Series, error message)
    _with_status: Whether to display progress bars during operations
  """

  def __init__(
    self,
    queries: t.List[Query],
    query_structure: QueryStructure,
    sample_data: t.Dict[str, pd.DataFrame],
    multi_processing: bool = True,
    with_status: bool = False,
  ):
    self._queries = queries
    self._query_structure = query_structure
    self._sample_data = sample_data
    self._results: t.List[QueryResult] = []
    self._multi_processing = multi_processing
    self._with_status = with_status

  def __len__(self) -> int:
    """Return the number of queries in the pool."""
    return len(self._queries)

  def __iter__(self) -> t.Iterator[Query]:
    """Iterate over the queries in the pool."""
    return iter(self._queries)

  def deduplicate(self) -> None:
    """
    Remove duplicate queries from the pool while preserving results.

    This method eliminates duplicate queries based on their string representation
    and complexity, considering multi-line and single-line formats as distinct.
    When duplicates are found, only the first occurrence is kept while maintaining
    the correct association between queries and their results.

    The method:
    1. Creates a set to track seen queries while preserving order
    2. Maintains the association between queries and their execution results
    3. Treats multi-line and single-line versions of the same query as distinct
    4. Preserves the original sorting by complexity if present

    Note:
      - Queries are considered equal if they have the same string representation
        and complexity score
      - The query's multi_line property is considered in equality comparison
      - If execution results exist, they are properly maintained for the
        deduplicated queries
    """
    seen = {}

    deduplicated_queries = []
    deduplicated_results = []

    if not self._results:
      for idx, query in enumerate(self._queries):
        query_key = (str(query), query.multi_line)
        if query_key not in seen:
          seen[query_key] = idx
          deduplicated_queries.append(query)
    else:
      for idx, (query, result) in enumerate(zip(self._queries, self._results)):
        query_key = (str(query), query.multi_line)
        if query_key not in seen:
          seen[query_key] = idx
          deduplicated_queries.append(query)
          deduplicated_results.append(result)

    self._queries = deduplicated_queries

    if self._results:
      self._results = deduplicated_results

  @staticmethod
  def _execute_multi_line_query(
    query: Query, sample_data: t.Dict[str, pd.DataFrame]
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

  @staticmethod
  def _execute_single_query(query: Query, sample_data: t.Dict[str, pd.DataFrame]) -> QueryResult:
    """Execute a single query and handle any errors."""
    try:
      if query.multi_line:
        return QueryPool._execute_multi_line_query(query, sample_data)
      result = pd.eval(str(query), local_dict=sample_data)
      if isinstance(result, (pd.DataFrame, pd.Series)):
        return result, None
      return None, f'Result was not a DataFrame or Series: {type(result)}'
    except Exception as e:
      return None, f'{type(e).__name__}: {str(e)}'

  def execute(
    self,
    force_execute: bool = False,
    num_processes: t.Optional[int] = None,
  ) -> t.List[QueryResult]:
    """
    Execute all queries against the sample data, either in parallel or sequentially.

    Evaluates queries using either multiprocessing for parallel execution or
    sequential processing. Results are cached to avoid re-execution unless
    explicitly requested.

    Args:
      force_execute: If True, re-execute all queries even if results exist
      num_processes:
        Number of parallel processes to use. Defaults to CPU count.
        Only used when multi_processing is True.

    Returns:
      List of tuples containing (result, error) for each query
    """
    if len(self._queries) == 0:
      return []

    if len(self._results) > 0 and not force_execute:
      return self._results

    f = partial(self._execute_single_query, sample_data=self._sample_data)

    if self._multi_processing:
      ctx = mp.get_context('fork')

      with ctx.Pool(num_processes) as pool:
        iterator = pool.imap(f, self._queries)

        if self._with_status:
          iterator = tqdm(
            iterator, total=len(self._queries), desc='Executing queries', unit='query'
          )

        self._results = list(iterator)
    else:
      if self._with_status:
        iterator = tqdm(self._queries, desc='Executing queries', unit='query')
      else:
        iterator = self._queries

      self._results = [f(query) for query in iterator]

    return self._results

  def filter(
    self,
    filter_type: QueryFilter,
    force_execute: bool = False,
  ) -> None:
    """
    Filter queries based on their execution results.

    Modifies the query pool in-place to keep only queries matching the filter
    criteria. Executes queries if results don't exist.

    Args:
      filter_type: Criteria for keeping queries (NON_EMPTY, EMPTY, etc.)
      force_execute: If True, re-execute queries before filtering
    """
    if not self._results or force_execute:
      self._results = self.execute()

    filtered_queries, filtered_results = [], []

    for query, result_tuple in zip(self._queries, self._results):
      result, error = result_tuple

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

    self._queries, self._results = filtered_queries, filtered_results

  def items(self) -> t.Iterator[tuple[Query, QueryResult]]:
    """
    Iterate over query-result pairs.

    Each iteration yields a tuple containing a query and its execution result.
    If results haven't been computed yet, executes the queries first.

    Yields:
      tuple[Query, QueryResult]: Pairs of (query, (result, error))
    """
    if not self._results:
      self.execute()
    return zip(self._queries, self._results)

  def results(self) -> t.Iterator[QueryResult]:
    """
    Iterate over query results.

    If results haven't been computed yet, executes the queries first.

    Yields:
        QueryResult: Pairs of (result, error) for each query
    """
    if not self._results:
      self.execute()
    return iter(self._results)

  def statistics(self, force_execute: bool = False) -> QueryStatistics:
    """
    Generate comprehensive statistics about the query pool.

    Analyzes query characteristics and execution results to measure how well
    the generated queries match the target parameters.

    Args:
      force_execute: If True, re-execute queries before analysis

    Returns:
      Statistics comparing actual vs. target characteristics
    """
    if not self._results or force_execute:
      self._results = self.execute()

    statistics = QueryStatistics(query_structure=self._query_structure)
    statistics.total_queries = len(self._queries)

    for query in self._queries:
      has_selection = has_projection = has_groupby = False
      selection_count = projection_count = groupby_count = 0

      for op in query.operations:
        match op:
          case Selection(conditions):
            has_selection = True
            selection_count = len(conditions)
          case Projection(columns):
            has_projection = True
            projection_count = len(columns)
          case GroupByAggregation(columns, _):
            has_groupby = True
            groupby_count = len(columns)
          case Merge():
            ...

      if has_selection:
        statistics.queries_with_selection += 1
        statistics.selection_conditions.append(selection_count)

      if has_projection:
        statistics.queries_with_projection += 1
        statistics.projection_columns.append(projection_count)

      if has_groupby:
        statistics.queries_with_groupby += 1
        statistics.groupby_columns.append(groupby_count)

      merge_count = query.merge_count

      if merge_count > 0:
        statistics.queries_with_merge += 1
        statistics.merge_count.append(merge_count)

    if self._results:
      for result, error in self._results:
        if error is not None:
          statistics.execution_results.failed += 1
          statistics.execution_results.errors[error] += 1
        else:
          statistics.execution_results.successful += 1
          if result is not None:
            if (isinstance(result, pd.DataFrame) and not result.empty) or (
              isinstance(result, pd.Series) and result.size > 0
            ):
              statistics.execution_results.non_empty += 1
            else:
              statistics.execution_results.empty += 1

    return statistics

  def save(self, output_file: str, create_dirs: bool = True) -> None:
    """
    Save all queries to a file.

    Each query is saved on a separate line in its string representation.
    Empty queries are filtered out and whitespace is trimmed.

    Args:
      output_file: Path to the output file
      create_dirs: If True, creates parent directories if needed
    """
    if create_dirs and os.path.dirname(output_file):
      os.makedirs(os.path.dirname(output_file), exist_ok=True)

    queries = filter(None, map(lambda q: str(q).strip(), self._queries))

    with open(output_file, 'w+') as f:
      f.write('\n\n'.join(queries))

  def sort(self) -> None:
    """
    Sort queries by their complexity.

    Orders queries based on their complexity score while maintaining the
    association between queries and their execution results if they exist.
    """
    if not self._results:
      self._queries = sorted(self._queries)
    else:
      pairs = list(zip(self._queries, self._results))
      pairs.sort(key=lambda x: x[0])
      self._queries, self._results = map(list, zip(*pairs))
