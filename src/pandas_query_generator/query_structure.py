import json
from dataclasses import dataclass


@dataclass
class QueryStructure:
  """
  A high-level structure describing meta-information about the generated queries.
  """

  allow_aggregation: bool
  allow_group_by: bool
  allow_projection: bool
  multi_line: bool
  num_merges: int
  num_queries: int
  num_selections: int

  @staticmethod
  def from_file(path: str) -> 'QueryStructure':
    with open(path, 'r') as file:
      content = json.load(file)

    return QueryStructure(
      allow_aggregation=content.get('allow_aggregation', False),
      allow_group_by=content.get('allow_group_by', False),
      multi_line=content.get('multi_line', False),
      num_merges=content.get('num_merges', 2),
      num_queries=content.get('num_queries', 2),
      num_selections=content.get('num_selections', 3),
      allow_projection=content.get('allow_projection', False),
    )
