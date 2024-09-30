import argparse
from dataclasses import dataclass


@dataclass
class Arguments:
  """
  A wrapper class providing concrete types for parsed command-line arguments.
  """

  output_directory: str
  params: str
  schema: str
  verbose: bool

  @staticmethod
  def from_args() -> 'Arguments':
    parser = argparse.ArgumentParser(description='Pandas Query Generator CLI')

    parser.add_argument(
      '--schema',
      type=str,
      required=True,
      help='Path to the relational schema JSON file',
    )

    parser.add_argument(
      '--params',
      type=str,
      required=True,
      help='Path to the user-defined parameters JSON file',
    )

    parser.add_argument(
      '--output-directory',
      type=str,
      required=False,
      default='./results',
      help='Directory to write results to',
    )

    parser.add_argument(
      '--verbose',
      type=bool,
      required=False,
      default=False,
      help='Whether or not to print extra generation information',
    )

    return Arguments(**vars(parser.parse_args()))
