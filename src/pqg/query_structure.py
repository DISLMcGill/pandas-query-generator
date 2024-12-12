from dataclasses import dataclass

from .arguments import Arguments


@dataclass
class QueryStructure:
  """
  Configuration parameters controlling query generation behavior.

  This class encapsulates the probability and limit settings that determine
  what kinds of queries are generated. It controls aspects like how likely
  different operations are to appear and how complex they can be.

  Attributes:
    groupby_aggregation_probability: Probability (0-1) of including a GROUP BY operation
    max_groupby_columns: Maximum number of columns that can be grouped on
    max_merges: Maximum number of table joins allowed in a query
    max_projection_columns: Maximum number of columns that can be selected
    max_selection_conditions: Maximum number of WHERE clause conditions
    projection_probability: Probability (0-1) of including a SELECT operation
    selection_probability: Probability (0-1) of including a WHERE operation
  """

  groupby_aggregation_probability: float
  max_groupby_columns: int
  max_merges: int
  max_projection_columns: int
  max_selection_conditions: int
  projection_probability: float
  selection_probability: float

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
      groupby_aggregation_probability=arguments.groupby_aggregation_probability,
      max_groupby_columns=arguments.max_groupby_columns,
      max_merges=arguments.max_merges,
      max_projection_columns=arguments.max_projection_columns,
      max_selection_conditions=arguments.max_selection_conditions,
      projection_probability=arguments.projection_probability,
      selection_probability=arguments.selection_probability,
    )
