import time
from contextlib import contextmanager

from .arguments import Arguments
from .generator import Generator
from .query_structure import QueryStructure
from .schema import Schema


def main() -> None:
  arguments = Arguments.from_args()

  schema, query_structure = Schema.from_file(arguments.schema), QueryStructure.from_args(arguments)

  generator = Generator(schema, query_structure, with_status=True)

  @contextmanager
  def timer(description: str):
    """Measure and print the execution time of a code block."""
    start = time.time()
    yield
    elapsed_time = time.time() - start
    print(f'Time taken for {description}: {elapsed_time:.2f} seconds')

  will_execute = arguments.verbose or arguments.filter is not None

  message = (
    f'generating and executing {arguments.num_queries} queries'
    if will_execute
    else f'generating {arguments.num_queries} queries'
  )

  with timer(message):
    query_pool = generator.generate(
      arguments.num_queries,
      arguments.multi_line,
      multi_processing=not arguments.disable_multi_processing,
    )

    if arguments.filter is not None:
      query_pool.filter(arguments.filter)

    if arguments.sort:
      query_pool.sort()

    if arguments.verbose:
      for i, (query, (result, error)) in enumerate(query_pool.items(), 1):
        print(f'Query {i}\n')
        print(str(query) + '\n')

        if result is not None:
          print('Results:\n')
          print(result)
        elif error is not None:
          print('Error:\n')
          print(error)

        print()

      print(query_pool.statistics())

    query_pool.save(arguments.output_file)

    print(f'\nQueries written to {arguments.output_file}')
