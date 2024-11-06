import typing as t
from dataclasses import dataclass

from .operation import Operation


@t.runtime_checkable
class Query(t.Protocol):
  entity: str
  operations: t.List[Operation]

  def __str__(self) -> str: ...

  def format_multi_line(self, start_counter: int = 1) -> t.Tuple[str, int]: ...

  @property
  def merge_entities(self) -> t.Set[str]: ...


@dataclass
class Merge(Operation):
  right: Query
  left_on: str
  right_on: str

  def apply(self, entity: str) -> str:
    return f'.merge({self.right}, left_on={self.left_on}, right_on={self.right_on})'

  @property
  def entities(self) -> t.Set[str]:
    """
    Get the set of all entities involved in the right side of this merge operation.

    This property provides a complete view of all tables involved in the right-hand
    side of the merge, including:
    1. The immediate right entity being merged
    2. Any entities that have been merged into the right entity through nested merges

    The difference between this and Query.merge_entities is that this property only
    tracks entities from the right side of the merge operation, while merge_entities
    includes the base entity and all merged entities from both sides.

    Returns:
      Set[str]:
        A set of entity names that are part of the right-hand side of
        this merge operation's join graph.
    """
    return {self.right.entity}.union(self.right.merge_entities)
