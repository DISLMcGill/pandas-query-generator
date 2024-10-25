import argparse
import typing as t
from dataclasses import dataclass


class HelpFormatter(argparse.HelpFormatter):
  """
  Custom help formatter that aligns option strings and help text with multi-line usage.
  """

  def __init__(
    self,
    prog: str,
    indent_increment: int = 2,
    max_help_position: int = 50,
    width: t.Optional[int] = None,
  ):
    super().__init__(prog, indent_increment, max_help_position, width)

  def _format_usage(self, usage, actions, groups, prefix) -> str:
    """
    Format usage section with one flag per line.
    """
    actions_str = ' '.join(
      f'[{a.option_strings[0]}]' if not a.required else f'{a.option_strings[0]}'
      for a in [a for a in actions if not isinstance(a, argparse._HelpAction)]
    )

    return f'usage: {self._prog} {actions_str}\n\n'

  def _format_action_invocation(self, action: argparse.Action) -> str:
    """
    Formats the action invocation with simplified display.
    """
    if not action.option_strings:
      return self._metavar_formatter(action, action.dest)(1)[0]

    if action.option_strings:
      if isinstance(action, argparse._HelpAction):
        return '-h --help'
      if action.nargs == 0:
        return action.option_strings[0]
      if action.required:
        return f'{action.option_strings[0]} {action.dest.lower()}'
      return action.option_strings[0]

    return ''

  def _format_action(self, action: argparse.Action) -> str:
    """
    Formats each action (argument) with help text.
    """
    help_text = (
      'Show this help message and exit'
      if isinstance(action, argparse._HelpAction)
      else (action.help or '')
    )

    if action.default is not None and action.default != argparse.SUPPRESS:
      if isinstance(action.default, bool):
        help_text = f'{help_text} (default: {str(action.default)})'
      else:
        help_text = f'{help_text} (default: {action.default})'

    return f'  {self._format_action_invocation(action)} {help_text}\n'


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
  sorted: bool
  verbose: bool

  @staticmethod
  def from_args() -> 'Arguments':
    parser = argparse.ArgumentParser(
      description='Pandas Query Generator CLI',
      formatter_class=HelpFormatter,
    )

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
      default=0,
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
      '--sorted',
      action='store_true',
      help='Whether or not to sort the queries by complexity',
    )

    parser.add_argument(
      '--verbose',
      action='store_true',
      help='Print extra generation information and statistics',
    )

    return Arguments(**vars(parser.parse_args()))
