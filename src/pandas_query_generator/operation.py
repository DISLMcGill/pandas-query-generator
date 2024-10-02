import typing as t
from abc import ABC, abstractmethod


class Operation(ABC):
  """
  Abstract base class for different types of DataFrame operations.

  This class provides a common interface for various operations that can be
  performed on a DataFrame, such as selection, projection, or aggregation.

  Attributes:
    df_name (str): The name of the DataFrame this operation is applied to.
    leading (bool): Indicates whether this operation is the first in a sequence.
    count (int, optional): A counter value, potentially used for naming or ordering operations.
  """

  def __init__(self, df_name: str, leading: bool, count: t.Optional[int] = None):
    """
    Initialize an Operation object.

    Args:
      df_name (str): The name of the DataFrame this operation is applied to.
      leading (bool): Whether this operation is the first in a sequence.
      count (int, optional): A counter value for the operation. Defaults to None.
    """
    self.df_name = df_name
    self.leading = leading
    self.count = count

  @abstractmethod
  def to_str(self) -> str:
    """
    Generate a string representation of the operation.

    This method should be implemented by subclasses to return the actual
    operation string in a format that can be executed on a DataFrame.

    Returns:
      str: A string representing the operation.
    """
    pass

  def exec(self) -> t.Any:
    """
    Execute the operation.

    This method evaluates the string representation of the operation.
    Caution: Using eval can be dangerous if the input is not properly sanitized.

    Returns:
      Any: The result of evaluating the operation.

    Raises:
      Exception: If the evaluation fails or produces an error.
    """
    try:
      return eval(self.to_str())
    except Exception as e:
      raise Exception(f'Error executing operation: {e}')

  def set_count(self, count: int) -> None:
    """
    Set the count value for the operation.

    Args:
      count (int): The new count value.
    """
    self.count = count

  def set_leading(self, is_leading: bool) -> None:
    """
    Set the leading status of the operation.

    Args:
      is_leading (bool): The new leading status.
    """
    self.leading = is_leading
