import multiprocessing as mp
import typing as t
from dataclasses import dataclass
from functools import partial

import pandas as pd
from tqdm import tqdm

from pqg.arguments import Arguments

from .query_builder import QueryBuilder
from .query_pool import QueryPool, QueryResult
from .query_structure import QueryStructure
from .schema import Schema


@dataclass
class GenerateOptions:
  ensure_non_empty: bool = False
  multi_line: bool = False
  multi_processing: bool = True
  num_queries: int = 1000

  @staticmethod
  def from_args(arguments: Arguments) -> 'GenerateOptions':
    return GenerateOptions(
      arguments.ensure_non_empty,
      arguments.multi_line,
      not arguments.disable_multi_processing,
      arguments.num_queries,
    )


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
    self.schema, self.query_structure = schema, query_structure

    entities = schema.entities

    if with_status:
      entities = tqdm(schema.entities, desc='Generating sample data', unit='entity')

    sample_data: t.Dict[str, pd.DataFrame] = {}

    for entity in entities:
      sample_data[entity.name] = entity.generate_dataframe()

    self.sample_data, self.with_status = sample_data, with_status

  @staticmethod
  def _generate_single_query(
    schema: Schema,
    query_structure: QueryStructure,
    sample_data: t.Dict[str, pd.DataFrame],
    generate_options: GenerateOptions,
    _,
  ):
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
    query = QueryBuilder(schema, query_structure, generate_options.multi_line).build()

    if generate_options.ensure_non_empty:
      result = QueryPool._execute_single_query(query, sample_data)

      def should_retry(result: QueryResult):
        df_result, error = result

        if error is not None or df_result is None:
          return True

        if isinstance(df_result, pd.DataFrame):
          return df_result.empty

        if isinstance(df_result, pd.Series):
          return df_result.size == 0

        return False

      while should_retry(result):
        query = QueryBuilder(schema, query_structure, generate_options.multi_line).build()
        result = QueryPool._execute_single_query(query, sample_data)

    return query

  def generate(self, options: GenerateOptions) -> QueryPool:
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
    f = partial(
      self._generate_single_query, self.schema, self.query_structure, self.sample_data, options
    )

    if options.multi_processing:
      with mp.Pool() as pool:
        generated_queries = pool.imap(f, range(options.num_queries))

        if self.with_status:
          generated_queries = tqdm(
            generated_queries,
            total=options.num_queries,
            desc='Generating queries',
            unit='query',
          )

        generated_queries = list(generated_queries)
    else:
      if self.with_status:
        iterator = tqdm(range(options.num_queries), desc='Generating queries', unit='query')
      else:
        iterator = range(options.num_queries)

      generated_queries = [f(i) for i in iterator]

    return QueryPool(
      generated_queries,
      self.query_structure,
      self.sample_data,
      options.multi_processing,
      self.with_status,
    )
