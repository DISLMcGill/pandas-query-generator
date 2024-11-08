import multiprocessing as mp
from functools import partial

from tqdm import tqdm

from pandas_query_generator.query_pool import QueryPool

from .query_builder import QueryBuilder
from .query_structure import QueryStructure
from .schema import Schema


class Generator:
  def __init__(self, schema: Schema, query_structure: QueryStructure):
    self.schema = schema
    self.query_structure = query_structure

  @staticmethod
  def _generate_single_query(schema, query_structure, multi_line, _):
    return QueryBuilder(schema, query_structure, multi_line).build()

  def generate(self, queries: int, multi_line=False, with_status: bool = False) -> QueryPool:
    f = partial(self._generate_single_query, self.schema, self.query_structure, multi_line)

    with mp.Pool() as pool:
      if not with_status:
        return QueryPool(list(pool.imap(f, range(queries))))

      return QueryPool(
        list(
          tqdm(
            pool.imap(f, range(queries)),
            total=queries,
            desc='Generating queries',
            unit='query',
          )
        )
      )
