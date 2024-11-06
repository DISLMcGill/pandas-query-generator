import typing as t
from dataclasses import dataclass
from enum import Enum

from .entity import Property, PropertyDate, PropertyEnum, PropertyFloat, PropertyInt, PropertyString
from .operation import Operation


class AggregationType(str, Enum):
  """Defines supported aggregation types and their compatibility."""

  MEAN = 'mean'
  SUM = 'sum'
  MIN = 'min'
  MAX = 'max'
  COUNT = 'count'
  MODE = 'mode'
  NUNIQUE = 'nunique'
  FIRST = 'first'
  LAST = 'last'

  @staticmethod
  def compatible_aggregations(property: Property) -> t.List[str]:
    """Get compatible aggregation types for a given property type."""
    match property:
      case PropertyInt() | PropertyFloat():
        return [
          AggregationType.MEAN.value,
          AggregationType.SUM.value,
          AggregationType.MIN.value,
          AggregationType.MAX.value,
          AggregationType.COUNT.value,
          AggregationType.NUNIQUE.value,
          AggregationType.FIRST.value,
          AggregationType.LAST.value,
        ]
      case PropertyString() | PropertyEnum():
        return [
          AggregationType.COUNT.value,
          AggregationType.MODE.value,
          AggregationType.NUNIQUE.value,
          AggregationType.FIRST.value,
          AggregationType.LAST.value,
        ]
      case PropertyDate():
        return [
          AggregationType.MIN.value,
          AggregationType.MAX.value,
          AggregationType.COUNT.value,
          AggregationType.NUNIQUE.value,
          AggregationType.FIRST.value,
          AggregationType.LAST.value,
        ]


@dataclass
class GroupByAggregation(Operation):
  """
  Represents a group by aggregation operation in a query.

  Attributes:
      group_by_columns: List of columns to group by
      agg_columns: Dictionary mapping column names to their aggregation functions
  """

  group_by_columns: t.List[str]
  agg_columns: t.Dict[str, str]

  def apply(self, entity: str) -> str:
    """Generate the pandas groupby operation string."""
    group_cols = ', '.join(f"'{col}'" for col in self.group_by_columns)

    aggs = [f'{col!r}: {func!r}' for col, func in self.agg_columns.items()]
    aggs_dict = '{' + ', '.join(aggs) + '}'

    return f'.groupby(by=[{group_cols}]).agg({aggs_dict})'
