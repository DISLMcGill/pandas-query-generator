import multiprocessing
import typing as t
from dataclasses import dataclass

import pandas as pd

from .query import Query
from .utils import execute_query


def execute_query_wrapper(args):
  query, sample_data = args
  return execute_query(query, sample_data)


@dataclass
class QueryPool:
  queries: t.List[Query]

  def execute(
    self, sample_data: t.Dict[str, pd.DataFrame]
  ) -> t.List[t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]]:
    with multiprocessing.Pool() as pool:
      return list(
        pool.imap(execute_query_wrapper, ((query, sample_data) for query in self.queries)),
      )
