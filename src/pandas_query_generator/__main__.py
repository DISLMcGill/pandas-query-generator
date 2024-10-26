import multiprocessing
import os
import time
from contextlib import contextmanager
from typing import List, Optional, Tuple, Union

import pandas as pd
from sortedcontainers import SortedSet
from tqdm import tqdm

from .arguments import Arguments, QueryFilter
from .generator import Generator
from .query import Query
from .query_structure import QueryStructure
from .schema import Schema
from .utils import execute_query, generate_query_statistics, print_statistics


def execute_query_wrapper(args):
  query, sample_data = args
  return execute_query(query, sample_data)


def filter_queries(
  queries: List[Query],
  results: List[Tuple[Optional[Union[pd.DataFrame, pd.Series]], Optional[str]]],
  filter_type: QueryFilter,
) -> Tuple[List[Query], List[Tuple[Optional[Union[pd.DataFrame, pd.Series]], Optional[str]]]]:
  """
  Filter queries based on their execution results.

  Args:
    queries: List of queries to filter
    results: List of query execution results and errors
    filter_type: Type of filter to apply

  Returns:
    Tuple containing:
    - List of queries that match the filter criteria
    - List of corresponding execution results
  """
  filtered_queries = []
  filtered_results = []

  for query, result_tuple in zip(queries, results):
    result, error = result_tuple
    match filter_type:
      case QueryFilter.NON_EMPTY:
        if result is not None and (
          (isinstance(result, pd.DataFrame) and not result.empty)
          or (isinstance(result, pd.Series) and result.size > 0)
        ):
          filtered_queries.append(query)
          filtered_results.append(result_tuple)
      case QueryFilter.EMPTY:
        if result is not None and (
          (isinstance(result, pd.DataFrame) and result.empty)
          or (isinstance(result, pd.Series) and result.size == 0)
        ):
          filtered_queries.append(query)
          filtered_results.append(result_tuple)
      case QueryFilter.HAS_ERROR:
        if error is not None:
          filtered_queries.append(query)
          filtered_results.append(result_tuple)
      case QueryFilter.WITHOUT_ERROR:
        if error is None:
          filtered_queries.append(query)
          filtered_results.append(result_tuple)

  return filtered_queries, filtered_results


def main():
  arguments = Arguments.from_args()

  schema, query_structure = (
    Schema.from_file(arguments.schema),
    QueryStructure.from_args(arguments),
  )

  sample_data = {entity: schema.entities[entity].generate_dataframe() for entity in schema.entities}

  generator = Generator(schema, query_structure, arguments.multi_line)

  @contextmanager
  def timer(description):
    start = time.time()
    yield
    elapsed_time = time.time() - start
    print(f'Time taken for {description}: {elapsed_time:.2f} seconds')

  should_execute = arguments.verbose or arguments.filter is not None
  message = (
    f'generating and executing {arguments.num_queries} queries'
    if should_execute
    else f'generating {arguments.num_queries} queries'
  )

  with timer(message):
    queries = generator.generate(arguments.num_queries)

    results = None

    if should_execute:
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

    if arguments.filter is not None:
      if results is None:
        raise ValueError('Results required for filtering but execution was skipped')

      queries, results = filter_queries(queries, results, arguments.filter)

      print(f'\nFiltered to {len(queries)} queries matching criteria: {arguments.filter}')

    if arguments.sorted:
      if results is not None:
        sorted_pairs = sorted(zip(queries, results), key=lambda x: x[0])
        queries, results = zip(*sorted_pairs)
        queries = list(queries)
        results = list(results)
      else:
        queries = SortedSet(queries)

    if os.path.dirname(arguments.output_file):
      os.makedirs(os.path.dirname(arguments.output_file), exist_ok=True)

    with open(arguments.output_file, 'w+') as f:
      f.write(
        '\n\n'.join(
          query
          for query in filter(
            lambda content: content != '', map(lambda query: str(query).strip(), queries)
          )
        )
      )

    if arguments.verbose and results:
      statistics = generate_query_statistics(queries, results)

      for i, ((result, error), query) in enumerate(zip(results, queries), 1):
        print(f'Query {i}:\n')
        print(str(query) + '\n')

        if result is not None:
          print('Results:\n')
          print(result)
        elif error is not None:
          print('Error:\n')
          print(error)

        print()

      print_statistics(statistics)

      # If no successful results, display error summary
      if statistics['execution_results']['non_empty_results'] == 0:
        print('\nNo queries produced non-empty results. Error summary:')
        error_counts = statistics['execution_results']['errors']
        for error, count in error_counts.most_common():
          print(f'\n{count} occurrences of:')
          print(error)
    else:
      print(f'\nQueries written to: {arguments.output_file}')

    print()
