import typing as t

from .operation import Operation


class Projection(Operation):
  """
  Represents a projection operation on a DataFrame.

  This class encapsulates the logic for creating and executing projection operations,
  which select specific columns from a DataFrame.

  Attributes:
    desire_columns (List[str]): The list of column names to be projected.
    length (int): The number of columns to be projected.

  Example Usage:
    projection = Projection('df_name', ['col1', 'col2'])
  """

  def __init__(
    self, df_name: str, columns: t.List[str], count: t.Optional[int] = None, leading: bool = True
  ):
    """
    Initialize a Projection object.

    Args:
      df_name (str): The name of the DataFrame to project from.
      columns (List[str]): The list of column names to be projected.
      count (Optional[int], optional): An optional count value. Defaults to None.
      leading (bool, optional): Whether this is the leading operation. Defaults to True.
    """
    super().__init__(df_name, leading, count)
    self.desire_columns = columns
    self.length = len(columns)

  def __str__(self) -> str:
    """
    Generate a human-readable string representation of the projection operation.

    Returns:
      str: A string describing the projection operation, including the DataFrame name
           and the columns to be projected.
    """
    return f'Projection: df_name = {self.df_name}, columns = {self.desire_columns}'

  def to_str(self) -> str:
    """
    Generate a string representation of the projection operation in pandas grammar.

    This method creates a string that can be evaluated to perform the projection operation
    on a DataFrame.

    Returns:
      str: A string representing the projection operation, executable in pandas.

    Example:
      If df_name is 'coach' and desire_columns are ['Role', 'National_name'],
      it returns: "coach[['Role', 'National_name']]"
    """
    res_str = f'{self.df_name}' if self.leading else ''
    columns_str = ', '.join(f"'{col}'" for col in self.desire_columns)
    return f'{res_str}[[{columns_str}]]'

  def new_projection(self, columns: t.List[str]) -> 'Projection':
    """
    Create a new Projection object with updated columns.

    This method allows for the creation of a new projection based on the current one,
    but with a different set of columns.

    Args:
      columns (List[str]): The new list of column names to project.

    Returns:
      Projection: A new Projection object with the updated columns.
    """
    return Projection(self.df_name, columns, self.count, self.leading)

  def exec(self) -> t.Any:
    """
    Execute the projection operation.

    This method evaluates the string representation of the projection operation.
    Caution: Using eval can be dangerous if the input is not properly sanitized.

    Returns:
      Any: The result of evaluating the projection operation.

    Raises:
      Exception: If the evaluation fails or produces an error.
    """
    try:
      return eval(self.to_str())
    except Exception as e:
      raise Exception(f'Error executing projection: {e}')
