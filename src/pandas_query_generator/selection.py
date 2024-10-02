import typing as t

from .condition import Condition
from .operation import Operation
from .operators import ComparisonOperator, ConditionalOperator


class Selection(Operation):
  """
  A class representing a selection operation on a DataFrame.

  This class encapsulates the logic for creating and executing selection operations,
  which filter rows in a DataFrame based on specified conditions.

  Attributes:
    conditions (List[Union[Condition, ConditionalOperator]]): The list of conditions and logical operators for the selection.

  Example Usage:
    selection = Selection('df_name', [Condition('col1', ComparisonOperator.GE, 1), ConditionalOperator.AND, Condition('col2', ComparisonOperator.LE, 2)])
  """

  def __init__(
    self,
    df_name: str,
    conditions: t.List[t.Union[Condition, ConditionalOperator]],
    count: t.Optional[int] = None,
    leading: bool = True,
  ):
    """
    Initialize a Selection object.

    Args:
      df_name (str): The name of the DataFrame.
      conditions (List[Union[Condition, ConditionalOperator]]): A list of conditions and logical operators.
      count (Optional[int], optional): An optional count value. Defaults to None.
      leading (bool, optional): Whether the selection is the first operation to be performed. Defaults to True.
    """
    super().__init__(df_name, leading, count)
    self.conditions = conditions

  def __str__(self) -> str:
    """
    Generate a string representation of the selection.

    Returns:
      str: A string representing the selection, including the DataFrame name and conditions.
    """
    return f'Selection: df_name = {self.df_name}, conditions = {[str(c) for c in self.conditions]}'

  def new_selection(self, new_cond: t.List[t.Union[Condition, ConditionalOperator]]) -> 'Selection':
    """
    Create a new Selection object with updated conditions.

    Args:
      new_cond (List[Union[Condition, ConditionalOperator]]): A new list of conditions and logical operators.

    Returns:
      Selection: A new Selection object with the updated conditions.
    """
    return Selection(self.df_name, new_cond, self.count, self.leading)

  def to_str(self, dataframe: str = 'F') -> str:
    """
    Generate a string representation of the selection operation in pandas grammar.

    This method creates a string that can be evaluated to perform the selection operation on a DataFrame.

    Args:
        dataframe (str, optional): An alternative DataFrame reference. Defaults to "F".

    Returns:
        str: A string representing the selection operation in pandas grammar.

    Examples:
      Single Condition: "df[condition]"
      Multiple Conditions: "df[(condition1) & (condition2)]"
    """
    res_str = f'{self.df_name}' if self.leading else ''

    if len(self.conditions) == 1:
      cur_condition = self._process_single_condition(self.conditions[0], dataframe)
    else:
      cur_condition = self._process_multiple_conditions(dataframe)

    return res_str + '[' + cur_condition + ']'

  def _process_single_condition(self, condition: Condition, df2: str) -> str:
    """
    Process a single condition for the selection operation.

    Args:
      condition (Condition): The condition to process.
      df2 (str): The DataFrame reference to use.

    Returns:
      str: A string representation of the processed condition.
    """
    df_ref = self.df_name if df2 == 'F' else df2

    if condition.op not in [ComparisonOperator.STARTS_WITH, ComparisonOperator.IN]:
      if isinstance(condition.val, str) and condition.val.count('-') == 2:
        return f"({df_ref}['{condition.col}'] {condition.op.value} '{condition.val}')"
      else:
        return f"({df_ref}['{condition.col}'] {condition.op.value} {condition.val})"
    elif condition.op == ComparisonOperator.IN:
      return f"({df_ref}['{condition.col}'].isin({condition.val}))"
    else:
      return f"({df_ref}['{condition.col}']{condition.op.value}('{condition.val}'))"

  def _process_multiple_conditions(self, df2: str) -> str:
    """
    Process multiple conditions for the selection operation.

    Args:
      df2 (str): The DataFrame reference to use.

    Returns:
      str: A string representation of the processed conditions.
    """
    conditions = []

    for condition in self.conditions:
      if isinstance(condition, ConditionalOperator):
        conditions.append(condition.value)
      else:
        conditions.append(self._process_single_condition(condition, df2))

    return ' '.join(conditions)

  def is_logically_consistent(self) -> bool:
    """
    Check if the conditions in the selection are logically consistent.

    This method ensures that the combined conditions don't contradict each other.

    Returns:
      bool: True if the conditions are consistent, otherwise False.
    """
    and_segments = self._split_conditions_by_or()

    for segment in and_segments:
      conditions_only = [c for c in segment if isinstance(c, Condition)]

      if not self._check_segment_consistency(conditions_only):
        return False

    return True

  def _split_conditions_by_or(self) -> t.List[t.List[t.Union[Condition, ConditionalOperator]]]:
    """
    Split the conditions into segments based on OR operators.

    Returns:
      List[List[Union[Condition, ConditionalOperator]]]: A list of condition segments.
    """
    and_segments = []

    current_segment = []

    for cond in self.conditions:
      if isinstance(cond, ConditionalOperator) and cond == ConditionalOperator.OR:
        if current_segment:
          and_segments.append(current_segment)
          current_segment = []
      else:
        current_segment.append(cond)

    if current_segment:
      and_segments.append(current_segment)

    return and_segments

  def _check_segment_consistency(self, conditions: t.List[Condition]) -> bool:
    """
    Check the logical consistency of a segment of conditions.

    Args:
      conditions (List[Condition]): A list of conditions to check for consistency.

    Returns:
      bool: True if the conditions are consistent, otherwise False.
    """
    for i, cond1 in enumerate(conditions):
      for j, cond2 in enumerate(conditions):
        if i != j and not cond1.is_consistent_with(cond2):
          return False

    return True
