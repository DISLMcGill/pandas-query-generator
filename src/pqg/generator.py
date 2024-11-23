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
  """
  Configuration options for query generation.

  Attributes:
    ensure_non_empty: If True, retry generation until queries produce non-empty results
    multi_line: If True, format generated queries across multiple lines
    multi_processing: If True, use parallel processing for query generation
    num_queries: Number of queries to generate
  """

  ensure_non_empty: bool = False
  multi_line: bool = False
  multi_processing: bool = True
  num_queries: int = 1000

  @staticmethod
  def from_args(arguments: Arguments) -> 'GenerateOptions':
    """
    Create GenerateOptions from command-line arguments.

    Args:
      arguments: Parsed command-line arguments

    Returns:
      GenerateOptions configured according to provided arguments
    """
    return GenerateOptions(
      arguments.ensure_non_empty,
      arguments.multi_line,
      not arguments.disable_multi_processing,
      arguments.num_queries,
    )


class Generator:
  """
  Generator for creating pools of pandas DataFrame queries.

  This class handles the generation of valid pandas DataFrame queries based on a provided
  schema and query structure parameters. It supports both parallel and sequential query
  generation with optional progress tracking.

  The generator can ensure that queries produce non-empty results by retrying failed
  generations, and supports formatting queries in both single-line and multi-line styles.

  Attributes:
    schema: Schema defining the database structure and relationships
    query_structure: Parameters controlling query complexity and features
    sample_data: Dictionary mapping entity names to sample DataFrames
    with_status: Whether to display progress bars during operations
  """

  def __init__(self, schema: Schema, query_structure: QueryStructure, with_status: bool = False):
    """
    Initialize generator with schema and generation parameters.

    Args:
      schema: Schema defining database structure and relationships
      query_structure: Parameters controlling query generation
      with_status: If True, display progress bars during operations
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
    Generate a single query, optionally ensuring non-empty results.

    This method creates a query using the provided schema and structure parameters.
    If ensure_non_empty is True, it will retry generation until the query produces
    a non-empty result when executed against the sample data.

    Args:
      schema: Database schema containing entity definitions
      query_structure: Parameters controlling query complexity and features
      sample_data: Sample DataFrames for testing query results
      generate_options: Configuration options for generation
      _: Ignored parameter (required for parallel mapping)

    Returns:
      Query: A randomly generated query conforming to the schema and structure

    Note:
      When ensure_non_empty is True, this method may enter an indefinite loop
      if it cannot generate a query producing non-empty results.
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
    Generate a pool of queries using parallel or sequential processing.

    This method creates multiple queries according to the specified options,
    either concurrently using a process pool or sequentially. Progress is
    tracked with a progress bar when with_status is True.

    Args:
      options: Configuration options controlling generation behavior

    Returns:
      QueryPool containing the generated queries and sample data

    Note:
      When using parallel processing, the progress bar accurately tracks
      completion across all processes. The resulting QueryPool contains
      all successfully generated queries in an arbitrary order.
    """
    f = partial(
      self._generate_single_query, self.schema, self.query_structure, self.sample_data, options
    )

    if options.multi_processing:
      with mp.Pool() as pool:
        generated_queries = list(
          tqdm(
            pool.imap(f, range(options.num_queries)),
            desc='Generating queries',
            disable=not self.with_status,
            total=options.num_queries,
            unit='query',
          )
        )
    else:
      generated_queries = [
        f(i)
        for i in tqdm(
          range(options.num_queries),
          desc='Generating queries',
          disable=not self.with_status,
          unit='query',
        )
      ]

    return QueryPool(
      generated_queries,
      self.query_structure,
      self.sample_data,
      options.multi_processing,
      self.with_status,
    )
