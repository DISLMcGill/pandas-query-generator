import typing as t
from dataclasses import dataclass, field

from .operation import Operation


@dataclass
class Selection(Operation):
  """
  Represents a selection operation in a query.

  Attributes:
  conditions (List[Tuple[str, str, Any, str]]): List of selection conditions and operators.
    Each tuple contains (column, operation, value, next_condition_operator).
    The last tuple's next_condition_operator is ignored.
  """

  conditions: t.List[t.Tuple[str, str, t.Any, str]] = field(default_factory=list)

  def apply(self, entity: str) -> str:
    if not self.conditions:
      return ''

    formatted_conditions = []

    for i, (col, op, val, next_op) in enumerate(self.conditions):
      if op in ['.str.startswith', '.isin']:
        condition = f'({entity}[{col}]{op}({val}))'
      else:
        condition = f'({entity}[{col}] {op} {val})'

      if i < len(self.conditions) - 1:
        condition += f' {next_op} '

      formatted_conditions.append(f'{condition}')

    return f"[{''.join(formatted_conditions)}]"
