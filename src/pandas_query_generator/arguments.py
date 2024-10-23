import argparse
from dataclasses import dataclass


@dataclass
class Arguments:
  """
  A wrapper class providing concrete types for parsed command-line arguments.
  """

  multi_line: bool
  num_queries: int
  output_file: str
  query_structure: str
  schema: str
  verbose: bool

  @staticmethod
  def from_args() -> 'Arguments':
    parser = argparse.ArgumentParser(description='Pandas Query Generator CLI')

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
      '--query-structure',
      type=str,
      required=True,
      help='Path to the user-defined query structure JSON file',
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
