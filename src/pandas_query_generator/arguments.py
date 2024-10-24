import argparse
from dataclasses import dataclass


@dataclass
class Arguments:
  """
  A wrapper class providing concrete types for parsed command-line arguments.
  """

  max_groupby_columns: int
  max_merges: int
  max_projection_columns: int
  max_selection_conditions: int
  multi_line: bool
  num_queries: int
  output_file: str
  schema: str
  verbose: bool

  @staticmethod
  def from_args() -> 'Arguments':
    parser = argparse.ArgumentParser(description='Pandas Query Generator CLI')

    parser.add_argument(
      '--max-groupby-columns',
      type=int,
      required=False,
      default=0,
      help='Maximum number of columns in group by operations',
    )

    parser.add_argument(
      '--max-merges',
      type=int,
      required=False,
      default=2,
      help='Maximum number of table merges allowed',
    )

    parser.add_argument(
      '--max-projection-columns',
      type=int,
      required=False,
      default=0,
      help='Maximum number of columns to project',
    )

    parser.add_argument(
      '--max-selection-conditions',
      type=int,
      required=False,
      default=2,
      help='Maximum number of conditions in selection operations',
    )

    parser.add_argument(
      '--multi-line',
      action='store_true',
      help='Format queries on multiple lines',
    )

    parser.add_argument(
      '--num-queries',
      type=int,
      required=True,
      help='The number of queries to generate',
    )

    parser.add_argument(
      '--output-file',
      type=str,
      required=False,
      default='queries.txt',
      help='The name of the file to write the results to',
    )

    parser.add_argument(
      '--schema',
      type=str,
      required=True,
      help='Path to the relational schema JSON file',
    )

    parser.add_argument(
      '--verbose',
      action='store_true',
      help='Print extra generation information',
    )

    return Arguments(**vars(parser.parse_args()))
