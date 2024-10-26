import typing as t
from dataclasses import dataclass

from .operation import Operation


@t.runtime_checkable
class Query(t.Protocol):
  operations: t.List[Operation]

  def __str__(self) -> str: ...

  def format_multi_line(self, start_counter: int = 1) -> t.Tuple[str, int]: ...


@dataclass
class Merge(Operation):
  right: Query
  left_on: str
  right_on: str

  def apply(self, entity: str) -> str:
    return f'.merge({self.right}, left_on={self.left_on}, right_on={self.right_on})'
