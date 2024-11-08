import time
from contextlib import contextmanager

from tqdm import tqdm

from .arguments import Arguments
from .generator import Generator
from .query_structure import QueryStructure
from .schema import Schema


def main() -> None:
  arguments = Arguments.from_args()

  schema, query_structure = Schema.from_file(arguments.schema), QueryStructure.from_args(arguments)

  generator = Generator(schema, query_structure)

  sample_data = {}

  for entity in tqdm(schema.entities, desc='Generating sample data', unit='entity'):
    sample_data[entity.name] = entity.generate_dataframe()

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
      arguments.num_queries, multi_line=arguments.multi_line, with_status=True
    )

    if arguments.filter is not None:
      query_pool.filter(sample_data, arguments.filter, with_status=True)

    if arguments.sort:
      query_pool.sort()

    if arguments.verbose:
      query_pool.print_statistics(sample_data, with_status=True)

    query_pool.save(arguments.output_file)

    print(f'\nQueries written to {arguments.output_file}')
