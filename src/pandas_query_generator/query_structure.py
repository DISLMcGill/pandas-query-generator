from dataclasses import dataclass

from .arguments import Arguments


@dataclass
class QueryStructure:
  """
  A dataclass that encapsulates the configuration parameters controlling query generation.
  Contains settings for various query features like aggregation, projection, and merging.
  """

  max_groupby_columns: int
  max_merges: int
  max_projection_columns: int
  max_selection_conditions: int

  @staticmethod
  def from_args(arguments: Arguments) -> 'QueryStructure':
    """
    Create a QueryStructure instance from command-line arguments.

    Args:
      arguments: Instance of Arguments containing parsed command-line parameters

    Returns:
      QueryStructure: Instance configured according to the provided arguments
    """
    return QueryStructure(
      max_groupby_columns=arguments.max_groupby_columns,
      max_merges=arguments.max_merges,
      max_projection_columns=arguments.max_projection_columns,
      max_selection_conditions=arguments.max_selection_conditions,
    )
