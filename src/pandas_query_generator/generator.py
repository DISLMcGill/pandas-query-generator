import multiprocessing as mp
from functools import partial

from tqdm import tqdm

from pandas_query_generator.query_pool import QueryPool

from .query_builder import QueryBuilder
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

  def generate(self, queries: int, multi_line=False) -> QueryPool:
    """
    Generate a pool of queries using parallel processing.

    Creates multiple queries concurrently using a process pool. Each query is
    randomly generated according to the schema and query structure parameters.

    Args:
      queries: Number of queries to generate
      multi_line: Whether to format queries across multiple lines

    Returns:
      QueryPool: A pool containing the generated queries and their sample data
    """
    f = partial(self._generate_single_query, self.schema, self.query_structure, multi_line)

    with mp.Pool() as pool:
      generated_queries = pool.imap(f, range(queries))

      if self.with_status:
        generated_queries = tqdm(
          generated_queries,
          total=queries,
          desc='Generating queries',
          unit='query',
        )

      return QueryPool(
        list(generated_queries), self.query_structure, self.sample_data, self.with_status
      )
