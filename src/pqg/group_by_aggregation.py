import typing as t
from dataclasses import dataclass

from .operation import Operation


@dataclass
class GroupByAggregation(Operation):
  group_by_columns: t.List[str]
  agg_function: str

  def apply(self, entity: str) -> str:
    group_cols = ', '.join(f"'{col}'" for col in self.group_by_columns)
    numeric_only = 'numeric_only=True' if self.agg_function != 'count' else ''
    formatted_option = f', {numeric_only}' if numeric_only else ''
    return f".groupby(by=[{group_cols}]).agg('{self.agg_function}'{formatted_option})"
