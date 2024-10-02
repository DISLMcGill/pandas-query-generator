import typing as t

from .operation import Operation


class Merge(Operation):
  """
  Class representing a merge operation between two DataFrames or queries.
  Example usage:
      df1.merge(df2, left_on = , right_on = )
  """

  def __init__(
    self,
    df_name: str,
    queries: 'Query',
    count=None,
    on=None,
    left_on: str | None = None,
    right_on: str | None = None,
    leading=False,
  ):
    """
    Initialize a merge object.

    :param df_name: The name of the primary DataFrame.
    :param queries: The secondary pandas_query object to merge with.
    :param count: An optional count value.
    :param on: Column names to join on if both DataFrames share the same column names.
    :param left_on: The column name in the primary DataFrame to merge on.
    :param right_on: The column name in the secondary DataFrame to merge on.
    :param leading: Whether the merge is the first operation to be performed.
    """
    super().__init__(df_name, leading, count)
    self.operations = queries.operations
    self.queries = queries
    self.on_col = on if on is not None else []
    self.left_on = left_on if left_on is not None else ''
    self.right_on = right_on if right_on is not None else ''

  def to_str(self) -> str:
    """
    Generate a string representation of the merge operation.

    :return: A string that is executable in pandas grammar.
    """
    # If merging on the same column name
    if len(self.on_col) > 0:
      res_str = f'{self.df_name}' if self.leading else ''
      operations_to_str = self.queries.query_string
      on_cols = ','.join([f"'{col}'" for col in self.on_col])

      res_str += f'.merge({operations_to_str}, on=[{on_cols}])'
      return res_str

    # If merging on different column names
    else:
      res_str = f'{self.df_name}' if self.leading else ''
      operations_to_str = self.queries.query_string

      res_str += (
        f".merge({operations_to_str}, left_on='{self.left_on}', right_on='{self.right_on}')"
      )
      return res_str

  def new_merge(
    self,
    new_queries: 'Query',
    new_on_col=None,
    new_left_on=None,
    new_right_on=None,
  ) -> 'Merge':
    """
    Create a new merge object with updated queries and column names.

    :param new_queries: The new pandas_query object to merge with.
    :param new_on_col: Optional new list of column names to join on.
    :param new_left_on: Optional new column name in the primary DataFrame to merge on.
    :param new_right_on: Optional new column name in the secondary DataFrame to merge on.
    :return: A new merge object.
    """
    return Merge(
      self.df_name,
      new_queries,
      count=self.count,
      on=new_on_col,
      left_on=new_left_on,
      right_on=new_right_on,
      leading=self.leading,
    )

  def exec(self) -> t.Any:
    """
    Execute the merge operation.

    :return: The result of evaluating the merge operation.
    """
    return eval(self.to_str())

  def __str__(self) -> str:
    """
    Generate a string representation of the merge operation.

    :return: A string representing the merge operation.
    """
    return f'merge: df_name = {self.df_name}, on_col = {self.on_col}, left_on = {self.left_on}, right_on = {self.right_on}'
