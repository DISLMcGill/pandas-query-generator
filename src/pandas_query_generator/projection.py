import typing as t
from dataclasses import dataclass, field

from .operation import Operation


@dataclass
class Projection(Operation):
  """
  Represents a projection operation in a query.

  Attributes:
    columns (List[str]): List of column names to project.
  """

  columns: t.List[str] = field(default_factory=list)

  def apply(self, entity: str) -> str:
    return f"[[{', '.join(repr(col) for col in self.columns)}]]"
