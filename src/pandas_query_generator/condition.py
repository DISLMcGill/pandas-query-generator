from .operators import ComparisonOperator


class Condition:
  """
  Represents a condition in a dataframe query, such as 'column > value'.

  This class encapsulates the components of a condition: the column name,
  the comparison operator, and the value to compare against.

  Attributes:
    col (str): The name of the column to apply the condition to.
    op (ComparisonOperator): The comparison operator to use.
    val (Any): The value to compare against. Can be a number, string, or other types.
  """

  def __init__(self, col_name: str, op: ComparisonOperator, val):
    """
    Initialize a new Condition.

    Args:
      col_name (str): The name of the column to apply the condition to.
      op (ComparisonOperator): The comparison operator to use.
      val (Any): The value to compare against. Can be a number, string, or other types.
    """
    self.col = col_name
    self.op = op
    self.val = val

  def __str__(self) -> str:
    """
    Return a string representation of the Condition.

    Returns:
      str: A string in the format 'Condition(column, operator, value)'.
    """
    return f'Condition({self.col}, {self.op.value}, {self.val})'

  def replace_val(self, val):
    """
    Create a new Condition with the same column and operator, but a different value.

    Args:
      val (Any): The new value to use in the condition.

    Returns:
      Condition: A new Condition object with the updated value.
    """
    return Condition(self.col, self.op, val)

  def replace_op(self, op: ComparisonOperator):
    """
    Create a new Condition with the same column and value, but a different operator.

    Args:
      op (ComparisonOperator): The new operator to use in the condition.

    Returns:
      Condition: A new Condition object with the updated operator.
    """
    return Condition(self.col, op, self.val)

  def is_consistent_with(self, other: 'Condition') -> bool:
    """
    Check if this condition is logically consistent with another condition.

    Two conditions are considered consistent if they don't contradict each other.
    For example, (x > 5) and (x < 3) are not consistent.

    Args:
      other (Condition): The other condition to compare with.

    Returns:
      bool: True if the conditions are consistent, False otherwise.

    Note:
      Conditions on different columns are always considered consistent.
    """
    # Conditions on different columns are always consistent
    if self.col != other.col:
      return True

    # Check for logical consistency between the two conditions
    if self.col == other.col:
      return not any(
        [
          (
            self.op in [ComparisonOperator.LE, ComparisonOperator.LT]
            and other.op in [ComparisonOperator.GE, ComparisonOperator.GT]
            and self.val <= other.val
          ),
          (
            self.op in [ComparisonOperator.GE, ComparisonOperator.GT]
            and other.op in [ComparisonOperator.LE, ComparisonOperator.LT]
            and self.val >= other.val
          ),
          (
            self.op == ComparisonOperator.EQ
            and other.op in [ComparisonOperator.LT, ComparisonOperator.LE]
            and self.val >= other.val
          ),
          (
            self.op == ComparisonOperator.EQ
            and other.op in [ComparisonOperator.GT, ComparisonOperator.GE]
            and self.val <= other.val
          ),
          (
            self.op in [ComparisonOperator.LT, ComparisonOperator.LE]
            and other.op == ComparisonOperator.EQ
            and self.val <= other.val
          ),
          (
            self.op in [ComparisonOperator.GT, ComparisonOperator.GE]
            and other.op == ComparisonOperator.EQ
            and self.val >= other.val
          ),
          (
            self.op == ComparisonOperator.EQ
            and other.op == ComparisonOperator.NE
            and self.val == other.val
          ),
          (
            self.op == ComparisonOperator.NE
            and other.op == ComparisonOperator.EQ
            and self.val == other.val
          ),
          (
            self.op == ComparisonOperator.EQ
            and other.op == ComparisonOperator.EQ
            and self.val != other.val
          ),
          (
            self.op == ComparisonOperator.STARTS_WITH
            and other.op == ComparisonOperator.STARTS_WITH
            and self.val != other.val
          ),
          (
            self.op == ComparisonOperator.IN
            and other.op == ComparisonOperator.IN
            and self.val != other.val
          ),
        ]
      )

    return True
