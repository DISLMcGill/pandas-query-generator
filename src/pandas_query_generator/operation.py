import typing as t
from abc import abstractmethod


@t.runtime_checkable
class Operation(t.Protocol):
  """
  Abstract base class for query operations.
  """

  @abstractmethod
  def apply(self, entity: str) -> str:
    """
    Apply the operation to the given entity.

    Args:
      entity (str): The name of the entity to apply the operation to.

    Returns:
      str: The string representation of the applied operation.
    """
    ...
