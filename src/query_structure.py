import json
from dataclasses import dataclass


@dataclass
class QueryStructure:
  """
  A high-level structure describing meta-information about the generated queries.
  """

  aggregation: bool
  group_by: bool
  multi_line: bool
  num_merges: int
  num_queries: int
  num_selections: int
  projection: bool

  @staticmethod
  def from_file(path: str) -> 'QueryStructure':
    with open(path, 'r') as file:
      content = json.load(file)

    return QueryStructure(
      aggregation=content.get('aggregation', False),
      group_by=content.get('group_by', False),
      multi_line=content.get('multi_line', False),
      num_merges=content.get('num_merges', 2),
      num_queries=content.get('num_queries', 2),
      num_selections=content.get('num_selections', 3),
      projection=content.get('projection', False),
    )
