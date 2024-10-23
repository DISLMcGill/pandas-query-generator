import multiprocessing
import typing as t
from functools import partial

from tqdm import tqdm

from .query import Query
from .query_builder import QueryBuilder
from .query_structure import QueryStructure
from .schema import Schema


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema = schema
    self.query_structure = query_structure

  @staticmethod
  def _generate_single_query(schema, query_structure, _):
    return QueryBuilder(schema, query_structure).build()

  def generate(self, queries: int) -> t.List[Query]:
    with multiprocessing.Pool() as pool:
      generate_func = partial(self._generate_single_query, self.schema, self.query_structure)

      return list(
        tqdm(
          pool.imap(generate_func, range(queries)),
          total=queries,
          desc='Generating queries',
          unit='query',
        )
      )
