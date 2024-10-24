import multiprocessing
import os
import time
from contextlib import contextmanager

from sortedcontainers import SortedSet
from tqdm import tqdm

from .arguments import Arguments
from .generator import Generator
from .query_structure import QueryStructure
from .schema import Schema
from .utils import execute_query, generate_query_statistics, print_statistics


def execute_query_wrapper(args):
  query, sample_data = args
  return execute_query(query, sample_data)


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

  with timer(f'Generating and executing {arguments.num_queries} queries'):
    queries = generator.generate(arguments.num_queries)

    if arguments.sorted:
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

    if arguments.verbose:
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

      stats = generate_query_statistics(queries, results)

      for i, ((result, error), query) in enumerate(zip(results, queries), 1):
        print(f'Query {i}:\n')
        print(str(query) + '\n')

        if result is not None:
          print('Results:')
          print(result)
        elif error:
          print('Error:\n')
          print(error)

        print()

      print_statistics(stats)

      # If no successful results, display error summary
      if stats['execution_results']['non_empty_results'] == 0:
        print('\nNo queries produced non-empty results. Error summary:')
        error_counts = stats['execution_results']['errors']
        for error, count in error_counts.most_common():
          print(f'\n{count} occurrences of:')
          print(error)
    else:
      print(f'\nQueries written to: {arguments.output_file}')

    print()
