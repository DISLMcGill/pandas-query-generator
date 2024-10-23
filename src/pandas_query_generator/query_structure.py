import json
from dataclasses import dataclass


@dataclass
class QueryStructure:
  """
  A high-level structure describing meta-information about the generated queries.
  """

  allow_groupby_aggregation: bool
  allow_projection: bool
  max_groupby_columns: int
  max_merges: int
  max_projection_columns: int
  max_selection_conditions: int
  multi_line: bool

  @staticmethod
  def from_file(path: str) -> 'QueryStructure':
    """
    Create a QueryStructure instance from a JSON file.

    Args:
        path: Path to the JSON configuration file

    Returns:
        QueryStructure: Instance configured according to the file
    """
    with open(path, 'r') as file:
      content = json.load(file)

    return QueryStructure(
      allow_groupby_aggregation=content.get('allow_groupby_aggregation', False),
      allow_projection=content.get('allow_projection', False),
      max_groupby_columns=content.get('max_groupby_columns', 2),
      max_merges=content.get('max_merges', 2),
      max_projection_columns=content.get('max_projection_columns', 4),
      max_selection_conditions=content.get('max_selection_conditions', 2),
      multi_line=content.get('multi_line', False),
    )
