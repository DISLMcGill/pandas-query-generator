import typing as t
from abc import abstractmethod


@t.runtime_checkable
class Operation(t.Protocol):
  """
  Protocol defining the interface for query operations.

  All query operations (Selection, Projection, GroupBy, etc.) must implement
  this protocol to be compatible with the query builder and execution system.
  """

  @abstractmethod
  def apply(self, entity: str) -> str:
    """
    Apply the operation to the given entity name.

    Args:
      entity: Name of the entity (table) to apply the operation to.

    Returns:
      A pandas query string fragment representing this operation.
      For example: ".groupby(['col'])" or "[['col1', 'col2']]"
    """
    ...
