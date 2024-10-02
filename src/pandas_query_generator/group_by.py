import typing as t

from .operation import Operation


class GroupBy(Operation):
  """
  Represents a groupby operation on a DataFrame.

  This class encapsulates the logic for creating and executing groupby operations,
  which group rows based on specified column(s) in a DataFrame.

  Attributes:
    columns (List[str]): The column(s) to group by.
    other_args (str): Additional arguments for the pandas groupby function.

  Example Usage:
    groupby = GroupBy('df_name', ['col1', 'col2'])
  """

  def __init__(
    self,
    df_name: str,
    columns: t.Union[str, t.List[str]],
    count: t.Optional[int] = None,
    other_args: t.Optional[str] = None,
    leading: bool = False,
  ):
    """
    Initialize a GroupBy object.

    Args:
      df_name (str): The name of the DataFrame to group.
      columns (Union[str, List[str]]): The column(s) to group by. Can be a single column name or a list of column names.
      count (Optional[int], optional): An optional count value. Defaults to None.
      other_args (Optional[str], optional): Additional arguments for the pandas groupby function. Defaults to None.
      leading (bool, optional): Whether this is the leading operation. Defaults to False.
    """
    super().__init__(df_name, leading, count)
    self.columns = [columns] if isinstance(columns, str) else columns
    self.other_args = other_args

  def __str__(self) -> str:
    """
    Generate a human-readable string representation of the groupby operation.

    Returns:
      str: A string describing the groupby operation, including the columns to group by.
    """
    return f'GroupBy: columns = {self.columns}'

  def set_columns(self, columns: t.Union[str, t.List[str]]) -> None:
    """
    Set or update the columns to group by.

    Args:
      columns (Union[str, List[str]]): The column(s) to group by. Can be a single column name or a list of column names.
    """
    self.columns = [columns] if isinstance(columns, str) else columns

  def to_str(self) -> str:
    """
    Generate a string representation of the groupby operation in pandas grammar.

    This method creates a string that can be evaluated to perform the groupby operation
    on a DataFrame.

    Returns:
      str: A string representing the groupby operation, executable in pandas.

    Example:
      If df_name is 'df', columns are ['col1', 'col2'], and other_args is None,
      it returns: "df.groupby(by=['col1', 'col2'])"
    """
    other_args = self.other_args if self.other_args else ''
    res_str = f'{self.df_name}' if self.leading else ''
    columns_str = f"[{', '.join(f"'{col}'" for col in self.columns)}]"
    res_str += f'.groupby(by={columns_str}{other_args})'
    return res_str

  def new_groupby(self, columns: t.Union[str, t.List[str]]) -> 'GroupBy':
    """
    Create a new GroupBy object with updated columns.

    This method allows for the creation of a new groupby operation based on the current one,
    but with a different set of columns.

    Args:
      columns (Union[str, List[str]]): The new column(s) to group by.

    Returns:
      GroupBy: A new GroupBy object with the updated columns.
    """
    return GroupBy(
      self.df_name,
      columns,
      count=self.count,
      other_args=self.other_args,
      leading=self.leading,
    )

  def exec(self) -> t.Any:
    """
    Execute the groupby operation.

    This method evaluates the string representation of the groupby operation.
    Caution: Using eval can be dangerous if the input is not properly sanitized.

    Returns:
      Any: The result of evaluating the groupby operation.

    Raises:
      Exception: If the evaluation fails or produces an error.
    """
    try:
      return eval(self.to_str())
    except Exception as e:
      raise Exception(f'Error executing groupby operation: {e}')
