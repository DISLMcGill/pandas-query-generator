import multiprocessing as mp
from functools import partial

from tqdm import tqdm

from .query_builder import QueryBuilder
from .query_pool import QueryPool
from .query_structure import QueryStructure
from .schema import Schema


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure, with_status: bool = False):
    """
    Generator for creating pools of pandas DataFrame queries.

    This class handles the generation of valid DataFrame queries based on a provided
    schema and query structure parameters. It manages sample data generation and
    parallel query generation.

    Attributes:
      schema: Schema defining the database structure
      query_structure: Parameters controlling query generation
      sample_data: Dictionary of sample DataFrames for each entity
      with_status: Whether to display progress bars during operations
    """
    self.schema = schema
    self.query_structure = query_structure

    self.sample_data, entities = {}, schema.entities

    if with_status:
      entities = tqdm(schema.entities, desc='Generating sample data', unit='entity')

    for entity in entities:
      self.sample_data[entity.name] = entity.generate_dataframe()

    self.with_status = with_status

  @staticmethod
  def _generate_single_query(schema, query_structure, multi_line, _):
    """
    Generate a single query using provided parameters.

    Args:
      schema: Database schema containing entity definitions
      query_structure: Configuration parameters for query generation
      multi_line: Whether to format the query across multiple lines
      _: Ignored parameter (used for parallel mapping)

    Returns:
      Query: A randomly generated query conforming to the schema and structure
    """
    return QueryBuilder(schema, query_structure, multi_line).build()

  def generate(self, queries: int, multi_line=False, multi_processing=True) -> QueryPool:
    """
    Generate a pool of queries using either parallel or sequential processing.

    Creates multiple queries either concurrently using a process pool or
    sequentially based on the multi_processing parameter. Each query is
    randomly generated according to the schema and query structure parameters.

    Args:
      queries: Number of queries to generate
      multi_line: Whether to format queries across multiple lines
      multi_processing: Whether to use multiprocessing (default: True)

    Returns:
      QueryPool: A pool containing the generated queries and their sample data
    """
    f = partial(self._generate_single_query, self.schema, self.query_structure, multi_line)

    if multi_processing:
      with mp.Pool() as pool:
        generated_queries = pool.imap(f, range(queries))

        if self.with_status:
          generated_queries = tqdm(
            generated_queries,
            total=queries,
            desc='Generating queries',
            unit='query',
          )

        queries_list = list(generated_queries)
    else:
      if self.with_status:
        iterator = tqdm(range(queries), desc='Generating queries', unit='query')
      else:
        iterator = range(queries)

      queries_list = [f(i) for i in iterator]

    return QueryPool(
      queries_list, self.query_structure, self.sample_data, multi_processing, self.with_status
    )
