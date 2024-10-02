import typing as t

from .operation import Operation


class Aggregate(Operation):
  """
  Represents an aggregation operation on a DataFrame.

  This class encapsulates the logic for creating and executing aggregation operations,
  which compute summary statistics on specified columns in a DataFrame.

  Attributes:
    dict_key_vals (Union[str, Dict[str, str]]): Aggregation functions or a dictionary
        mapping columns to functions.

  Example Usage:
    aggregate = Aggregate('df_name', {'col1': 'mean', 'col2': 'sum'})
    aggregate = Aggregate('df_name', 'count')
  """

  def __init__(
    self,
    df_name: str,
    dict_columns: t.Union[str, t.Dict[str, str]],
    count: t.Optional[int] = None,
    leading: bool = True,
  ):
    """
    Initialize an Aggregate object.

    Args:
      df_name (str): The name of the DataFrame to aggregate.
      dict_columns (Union[str, Dict[str, str]]): Aggregation functions or a dictionary
          mapping columns to functions. Can be a string for simple aggregations like 'count'.
      count (Optional[int], optional): An optional count value. Defaults to None.
      leading (bool, optional): Whether this is the leading operation. Defaults to True.
    """
    super().__init__(df_name, leading, count)
    self.dict_key_vals = dict_columns

  def __str__(self) -> str:
    """
    Generate a human-readable string representation of the aggregation operation.

    Returns:
      str: A string describing the aggregation operation, including the aggregation functions.
    """
    return f'Aggregate: functions = {str(self.dict_key_vals)}'

  def to_str(self) -> str:
    """
    Generate a string representation of the aggregation operation in pandas grammar.

    This method creates a string that can be evaluated to perform the aggregation operation
    on a DataFrame.

    Returns:
      str: A string representing the aggregation operation, executable in pandas.

    Example:
      If df_name is 'df' and dict_key_vals is {'col1': 'mean', 'col2': 'sum'},
      it returns: "df.agg({'col1': 'mean', 'col2': 'sum'}, numeric_only=True)"
    """
    res_str = f'{self.df_name}' if self.leading else ''
    agg_str = (
      str(self.dict_key_vals) if isinstance(self.dict_key_vals, dict) else f"'{self.dict_key_vals}'"
    )
    res_str += f'.agg({agg_str}'
    if self.dict_key_vals != 'count':
      res_str += ', numeric_only=True'
    res_str += ')'
    return res_str

  def new_agg(self, dict_cols: t.Union[str, t.Dict[str, str]]) -> 'Aggregate':
    """
    Create a new Aggregate object with updated aggregation functions.

    This method allows for the creation of a new aggregation operation based on the current one,
    but with different aggregation functions.

    Args:
      dict_cols (Union[str, Dict[str, str]]): New aggregation functions or a dictionary
          mapping columns to functions.

    Returns:
      Aggregate: A new Aggregate object with the updated aggregation functions.
    """
    return Aggregate(self.df_name, dict_cols, count=self.count, leading=self.leading)

  def exec(self) -> t.Any:
    """
    Execute the aggregation operation.

    This method evaluates the string representation of the aggregation operation.
    Caution: Using eval can be dangerous if the input is not properly sanitized.

    Returns:
      Any: The result of evaluating the aggregation operation.

    Raises:
      Exception: If the evaluation fails or produces an error.
    """
    try:
      return eval(self.to_str())
    except Exception as e:
      raise Exception(f'Error executing aggregation operation: {e}')
