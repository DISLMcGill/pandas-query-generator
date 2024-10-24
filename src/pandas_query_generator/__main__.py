import multiprocessing
import os
import time
from contextlib import contextmanager

from tqdm import tqdm

from .arguments import Arguments
from .entity import *
from .generator import Generator
from .query_structure import QueryStructure
from .schema import Schema
from .utils import *


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

    os.makedirs(os.path.dirname(arguments.output_file), exist_ok=True)

    with open(arguments.output_file, 'w') as f:
      f.write('\n\n'.join(str(query) for query in queries))

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

      for i, (query, result) in enumerate(zip(queries, results), 1):
        print(f'Query {i}')
        print()
        print(query)
        print()
        print('Results:')
        print()
        print(result)

      print_statistics(generate_query_statistics(queries, results))
    else:
      print(f'\nQueries written to: {arguments.output_file}')


if __name__ == '__main__':
  main()
