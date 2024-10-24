import typing as t
from dataclasses import dataclass

from .operation import Operation


@dataclass
class Merge(Operation):
  right: t.Any
  left_on: str
  right_on: str

  def apply(self, entity: str) -> str:
    return f'.merge({self.right}, left_on={self.left_on}, right_on={self.right_on})'
