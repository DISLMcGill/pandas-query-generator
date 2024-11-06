import multiprocessing
import typing as t
from dataclasses import dataclass
from functools import partial

import pandas as pd
from tqdm import tqdm

from .query import Query
from .utils import execute_query


@dataclass
class QueryPool:
  queries: t.List[Query]

  def execute(
    self, sample_data: t.Dict[str, pd.DataFrame], with_status: bool = False
  ) -> t.List[t.Tuple[t.Optional[t.Union[pd.DataFrame, pd.Series]], t.Optional[str]]]:
    f = partial(execute_query, sample_data=sample_data)

    with multiprocessing.Pool() as pool:
      if not with_status:
        return list(pool.imap(f, self.queries))

      return list(
        tqdm(
          pool.imap(f, self.queries),
          total=len(self.queries),
          desc='Executing queries',
          unit='query',
        )
      )
