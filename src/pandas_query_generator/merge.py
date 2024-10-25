import typing as t
from dataclasses import dataclass

from .operation import Operation


@t.runtime_checkable
class String(t.Protocol):
  def __str__(self) -> str: ...


@dataclass
class Merge(Operation):
  right: String  # Any class that implements __str__
  left_on: str
  right_on: str

  def apply(self, entity: str) -> str:
    return f'.merge({self.right}, left_on={self.left_on}, right_on={self.right_on})'
