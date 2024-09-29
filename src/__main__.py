import itertools
import os
import random
import time
import warnings
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd
from pandas import Series
from tqdm import tqdm

warnings.filterwarnings('ignore', 'Boolean Series key will be reindexed to match DataFrame index.')


# do we use this class? not used
class Source:
  def __init__(self, df: pd.DataFrame):
    """
    Initialize a pandas_source object.

    :param df: The DataFrame to wrap.
    """
    self.source_df = df

    self.columns = df.columns
    self.range = self.generate_range()
    self.shape = df.shape
    self.description = df.describe()

  def generate_range(self) -> Dict[str, Union[str, List[Union[int, float]]]]:
    """
    Generate the data range (min and max values) for each numerical column.

    Iterates through each column in the DataFrame and checks its data type.
    If the column is numerical (integer, float, or date), it finds the minimum
    and maximum values in that column. Otherwise, it marks the range as "None".

    :return: A dictionary mapping column names to their data ranges.
             - Numerical columns have a range in the form of [min, max].
             - Non-numerical columns are mapped to the string "None".
    """
    column_data_range = {}

    for col in self.columns:
      dtype = self.source_df[col].dtypes
      if 'int' in str(dtype) or 'float' in str(dtype) or 'date' in str(dtype):
        cur_col_max = self.source_df[col].max()
        cur_col_min = self.source_df[col].min()
        column_data_range[col] = [cur_col_min, cur_col_max]
      else:
        column_data_range[col] = 'None'
    return column_data_range

  def merge(self, other: 'Source', left_on: str, right_on: str) -> 'Source':
    """
    Merge this DataFrame with another pandas_source object based on specified columns.

    This method wraps the Pandas `merge` method, merging the source DataFrame with
    another DataFrame on the specified columns.

    :param other: Another pandas_source object to merge with.
    :param left_on: The column name in this DataFrame to merge on.
    :param right_on: The column name in the other DataFrame to merge on.
    :return: A new pandas_source object containing the merged DataFrame.
    """
    # Merge the two DataFrames on the specified columns
    new_df = self.source_df.merge(other.source_df, left_on=left_on, right_on=right_on)

    # Return a new pandas_source object wrapping the merged DataFrame
    return Source(new_df)


class Operation:
  """
  The abstract base class for different types of DataFrame operations.

  Attributes:
      df_name (str): The name of the DataFrame.
      leading (bool): Whether the operation is the first to be performed.
      count (int or None): An optional count value for the operation.
  """

  def __init__(self, df_name: str, leading: bool, count: int = None):
    """
    Initialize an operation object.

    :param df_name: The name of the DataFrame.
    :param leading: Whether the operation is the first to be performed.
    :param count: An optional count value. (What does count represent?)
    """
    self.count = count
    self.df_name = df_name
    self.leading = leading

  def to_str(self) -> str:
    """
    Generate a string representation of the operation.

    This method should be overridden by subclasses to return the actual operation string.

    :return: A string representing the operation.
    """
    return ''

  def set_leading(self, b: bool):
    """
    Set the leading status of the operation.

    :param b: Boolean value to set the leading status.
    """
    self.leading = b

  def set_count(self, c: int):
    """
    Set the count value for the operation.

    :param c: Integer value to set the count.
    """
    self.count = c

  def exec(self) -> Any:
    """
    Execute the operation.

    This method calls `eval` on the string representation of the operation.

    :return: The result of evaluating the operation.
    """
    return eval(self.to_str())


class Operator(Enum):
  ge = '>='
  gt = '>'
  le = '<='
  lt = '<'
  eq = '=='
  ne = '!='
  startswith = '.str.startswith'
  in_op = 'in'


class ConditionalOperator(Enum):
  AND = '&'
  OR = '|'
  # NOT = "-"


class Condition:
  """
  Refers to conditions like 'col1 > 20' in a particular dataframe
  """

  def __init__(self, col_name, op: Operator, num):
    """

    :param col_name: str
    :param op: OP
    :param num: not only numbers, can also be strings
    """
    self.col = col_name
    self.op = op
    self.val = num

  def replace_val(self, val):
    return Condition(self.col, self.op, val)
    # self.val = val

  def replace_op(self, op):
    return Condition(self.col, op, self.val)
    # self.op = op

  def is_consistent_with(self, other: 'Condition') -> bool:
    """
    Check if the current condition is logically consistent with another condition.
    param other: The other condition to compare with.
    return: True if the conditions are consistent, otherwise False.
    """
    if self.col != other.col:
      return True  # Conditions on different columns are always consistent

    if self.col == other.col:
      # Check for logical consistency between the two conditions, avoid conditions like (x<3 and x>5)
      if (
        (
          self.op in [Operator.le, Operator.lt]
          and other.op in [Operator.ge, Operator.gt]
          and self.val <= other.val
        )
        or (
          self.op in [Operator.ge, Operator.gt]
          and other.op in [Operator.le, Operator.lt]
          and self.val >= other.val
        )
        or (
          self.op == Operator.eq
          and other.op in [Operator.lt, Operator.le]
          and self.val >= other.val
        )
        or (
          self.op == Operator.eq
          and other.op in [Operator.gt, Operator.ge]
          and self.val <= other.val
        )
        or (
          self.op in [Operator.lt, Operator.le]
          and other.op == Operator.eq
          and self.val <= other.val
        )
        or (
          self.op in [Operator.gt, Operator.ge]
          and other.op == Operator.eq
          and self.val >= other.val
        )
        or (self.op == Operator.eq and other.op in [Operator.ne] and self.val == other.val)
        or (self.op in [Operator.ne] and other.op == Operator.eq and self.val == other.val)
        or (self.op == Operator.eq and other.op == Operator.eq and self.val != other.val)
        or (
          self.op == Operator.startswith
          and other.op == Operator.startswith
          and self.val != other.val
        )
        or (self.op == Operator.in_op and other.op == Operator.in_op and self.val != other.val)
      ):
        return False

    return True

  def __str__(self):
    return f'condition ({self.col} {self.op.value} {self.val} )'


class Selection(Operation):
  """
  A class representing a selection operation on a DataFrame.

  Example Usage:
      selection(df_name, [condition(col1, OP.ge, 1), OP_cond.AND, condition(col2, OP.le, 2)])
  """

  def __init__(
    self,
    df_name: str,
    conditions: List[Union[Condition, ConditionalOperator]],
    count=None,
    leading=True,
  ):
    """
    Initialize a selection object.

    :param df_name: The name of the DataFrame.
    :param conditions: A list of conditions and logical operators.
    :param count: An optional count value.
    :param leading: Whether the selection is the first operation to be performed.
    """
    super().__init__(df_name, leading, count)
    self.conditions = conditions

  def new_selection(self, new_cond: List[Union[Condition, ConditionalOperator]]) -> 'Selection':
    """
    Create a new selection object with updated conditions.

    :param new_cond: A new list of conditions and logical operators.
    :return: A new selection object.
    """
    return Selection(self.df_name, new_cond, self.leading)

  def to_str(self, df2='F') -> str:
    """
    Generate a string representation of the selection operation.

    :param df2: An optional alternative DataFrame reference. Defaults to "F".
    :return: A string representing the selection operation in pandas grammar.

    Example (Single Condition):
        selection.to_str()
        # Returns: "df[condition]"

    Example (Multiple Conditions):
        selection.to_str()
        # Returns: "df[(condition1) & (condition2)]"
    """
    res_str = f'{self.df_name}' if self.leading else ''
    cur_condition = ''

    # Single Condition Case
    if len(self.conditions) == 1:
      cond = self.conditions[0]
      if df2.__eq__('F'):
        if cond.op.value != Operator.startswith.value and cond.op.value != Operator.in_op.value:
          if (
            isinstance(cond.val, str) and cond.val.count('-') == 2
          ):  # Check if value is a date string
            cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} '{cond.val}')"
          else:
            cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} {cond.val})"
        elif cond.op.value == Operator.in_op.value:
          cur_condition = f"({self.df_name}['{cond.col}'].isin({cond.val}))"
        else:
          cur_condition = f"({self.df_name}['{cond.col}']{cond.op.value}('{cond.val}'))"
      else:
        if cond.op.value != Operator.startswith.value and cond.op.value != Operator.in_op.value:
          if (
            isinstance(cond.val, str) and cond.val.count('-') == 2
          ):  # Check if value is a date string
            cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} '{cond.val}')"
          else:
            cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} {cond.val})"
        elif cond.op.value == Operator.in_op.value:
          cur_condition = f"({df2}['{cond.col}'].isin({cond.val}))"
        else:
          cur_condition = f"(df{df2}['{cond.col}']{cond.op.value}('{cond.val}'))"

      res_str = res_str + '[' + cur_condition + ']'
      return res_str

    # Multiple Conditions Case
    for i, condition in enumerate(self.conditions):
      cond = self.conditions[i]
      if isinstance(cond, ConditionalOperator):
        cur_condition += ' ' + cond.value + ' '
      else:
        if df2.__eq__('F'):
          if cond.op.value != Operator.startswith.value and cond.op.value != Operator.in_op.value:
            if (
              isinstance(cond.val, str) and cond.val.count('-') == 2
            ):  # Check if value is a date string
              cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} '{cond.val}')"
            else:
              cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} {cond.val})"
          elif cond.op.value == Operator.in_op.value:
            cur_condition += f"({self.df_name}['{cond.col}'].isin({cond.val}))"
          else:
            cur_condition += f"({self.df_name}['{cond.col}']{cond.op.value}('{cond.val}'))"
        else:
          if cond.op.value != Operator.startswith.value and cond.op.value != Operator.in_op.value:
            if (
              isinstance(cond.val, str) and cond.val.count('-') == 2
            ):  # Check if value is a date string
              cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} '{cond.val}')"
            else:
              cur_condition = f"({self.df_name}['{cond.col}'] {cond.op.value} {cond.val})"
          elif cond.op.value == Operator.in_op.value:
            cur_condition += f"(df{df2}['{cond.col}'].isin({cond.val}))"
          else:
            cur_condition += f"(df{df2}['{cond.col}']{cond.op.value}('{cond.val}'))"

    res_str = res_str + '[' + cur_condition + ']'
    return res_str

  def __str__(self) -> str:
    """
    Generate a string representation of the selection.

    :return: A string representing the selection.
    """
    conditions_ = [str(c) for c in self.conditions]
    return f'selection: df_name = {self.df_name} conditions = {conditions_}'

  def exec(self) -> Any:
    """
    Execute the selection operation.

    :return: The result of evaluating the selection.
    """
    return eval(self.to_str())

  def is_logically_consistent(self) -> bool:
    """
    Check if the conditions in the selection are logically consistent.
    return: True if the conditions are consistent, otherwise False.
    """
    and_segments = []
    current_segment = []

    # Separates the conditions based on | operators
    for cond in self.conditions:
      if isinstance(cond, ConditionalOperator) and cond == ConditionalOperator.OR:
        if current_segment:
          and_segments.append(current_segment)
          current_segment = []
      else:
        current_segment.append(cond)
    # Add the last segment
    if current_segment:
      and_segments.append(current_segment)
    # Check for logical consistency within each segment
    for segment in and_segments:
      conditions_only = [c for c in segment if isinstance(c, Condition)]
      for i, cond1 in enumerate(conditions_only):
        for j, cond2 in enumerate(conditions_only):
          if i != j and not cond1.is_consistent_with(cond2):
            return False

    return True


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
    left_on: str = None,
    right_on: str = None,
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

  def exec(self) -> Any:
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


class Projection(Operation):
  """
  Class representing a projection operation on a DataFrame.

  Example Usage:
      projection(df_name, ['col1', 'col2'])

  """

  def __init__(self, df_name: str, columns: List[str], count=None, leading=True):
    """
    Initialize a projection object.

    :param df_name: The name of the DataFrame.
    :param columns: The desired columns to be projected.
    :param count: An optional count value.
    :param leading: Whether it is the leading operation.
    """
    super().__init__(df_name, leading, count)
    self.desire_columns = columns
    self.length = len(columns)

  def to_str(self) -> str:
    """
    Generate a string representation of the projection operation.

    :return: A string that is executable in pandas grammar.
    """
    res_str = f'{self.df_name}' if self.leading else ''

    cur_str = ''
    for column in self.desire_columns:
      cur_str += "'" + column + "',"

    # Remove the last comma from the string
    cur_str = cur_str[:-1]

    # Example: coach[['Role', 'National_name']]
    res_str = res_str + '[[' + cur_str + ']]'

    return res_str

  def new_projection(self, columns: List[str]) -> 'Projection':
    """
    Create a new projection object with updated columns.

    :param columns: List of columns to project.
    :return: A new projection object.
    """
    return Projection(self.df_name, columns, self.leading)

  def __str__(self) -> str:
    """
    Generate a string representation of the projection operation.

    :return: A string representing the projection operation.
    """
    return f'projection: df_name = {self.df_name}, col = {self.desire_columns}'

  def exec(self) -> Any:
    """
    Execute the projection operation.

    :return: The result of evaluating the projection operation.
    """
    return eval(self.to_str())


class GroupBy(Operation):
  """
  Class representing a groupby operation on a DataFrame.

  Example Usage:
      group_by(df_name, ['col1', 'col2'])

  """

  def __init__(
    self,
    df_name: str,
    columns: Union[str, List[str]],
    count=None,
    other_args=None,
    leading=False,
  ):
    """
    Initialize a group_by object.

    :param df_name: The name of the DataFrame.
    :param columns: The columns to group by.
    :param count: An optional count value.
    :param other_args: Additional arguments for the pandas groupby function.
    :param leading: Whether it is the leading operation.
    """
    super().__init__(df_name, leading, count)
    self.columns = columns if isinstance(columns, List) else [columns]
    self.other_args = other_args

  def set_columns(self, columns: Union[str, List[str]]):
    """
    Set the columns to group by.

    :param columns: The columns to group by.
    """
    self.columns = columns if isinstance(columns, List) else [columns]

  def to_str(self) -> str:
    """
    Generate a string representation of the groupby operation.

    :return: A string that is executable in pandas grammar.
    """
    other_args = self.other_args if self.other_args else ''
    res_str = f'{self.df_name}' if self.leading else ''
    res_str += f'.groupby(by={self.columns}{other_args})'
    return res_str

  def new_groupby(self, columns: Union[str, List[str]]) -> 'GroupBy':
    """
    Create a new group_by object with updated columns.

    :param columns: The columns to group by.
    :return: A new group_by object.
    """
    return GroupBy(
      self.df_name,
      columns,
      count=self.count,
      other_args=self.other_args,
      leading=self.leading,
    )

  def __str__(self) -> str:
    """
    Generate a string representation of the groupby operation.

    :return: A string representing the groupby operation.
    """
    return f'groupby: {self.columns}'

  def exec(self) -> Any:
    """
    Execute the groupby operation.

    :return: The result of evaluating the groupby operation.
    """
    return eval(self.to_str())


class Aggregate(Operation):
  """
  Class representing an aggregation operation on a DataFrame.

  Example Usage:
      agg(df_name, {'col1': 'mean', 'col2': 'sum'})

  """

  def __init__(
    self,
    df_name: str,
    dict_columns: Union[str, Dict[str, str]],
    count=None,
    leading=True,
  ):
    """
    Initialize an agg object.

    :param df_name: The name of the DataFrame.
    :param dict_columns: Aggregation functions or a dictionary mapping columns to functions.
    :param count: An optional count value.
    :param leading: Whether it is the leading operation.
    """
    super().__init__(df_name, leading, count)
    self.dict_key_vals = dict_columns

  def to_str(self) -> str:
    """
    Generate a string representation of the aggregation operation.

    :return: A string that is executable in pandas grammar.
    """
    res_str = f'{self.df_name}' if self.leading else ''

    # Handle the aggregation function
    res_str = res_str + '.agg(' + "'" + str(self.dict_key_vals) + "'"
    if self.dict_key_vals != 'count':
      res_str += ', numeric_only=True'
    res_str += ')'

    return res_str

  def new_agg(self, dict_cols: Union[str, Dict[str, str]]) -> 'Aggregate':
    """
    Create a new agg object with updated aggregation functions.

    :param dict_cols: Aggregation functions or a dictionary mapping columns to functions.
    :return: A new agg object.
    """
    return Aggregate(self.df_name, dict_cols, leading=self.leading)

  def __str__(self) -> str:
    """
    Generate a string representation of the aggregation operation.

    :return: A string representing the aggregation operation.
    """
    return f'agg: {str(self.dict_key_vals)}'

  def exec(self) -> Any:
    """
    Execute the aggregation operation.

    :return: The result of evaluating the aggregation operation.
    """
    return eval(self.to_str())


class Query:
  """
  A class representing a pandas query in intermediate representation.

  Attributes:
      _source_ (TBL_source): The DataFrame or table source object.
      pre_gen_query (List[operation]): List of operations that form the query (executable)
      df_name (str): The name of the DataFrame before the operation.
      num_merges (int): Number of merges performed.
      operations (List[str]): List of supported operation types.
      query_string (str): The generated query string.
      merged (bool): Indicates if the query involves a merge operation.
      target (pd.DataFrame): The resulting DataFrame after applying the query operations.
  """

  def __init__(self, q_gen_query: List[Operation], source: 'TableSource', verbose=False):
    """
    Initialize a pandas_query object.

    :param q_gen_query: List of query operations (of type `operation`).
    :param source: The DataFrame or TBL_source object that is the target of the query.
    :param verbose: Whether to print the query string.
    """

    if verbose:
      print(self.get_query_string())
    # self._source_ = source # df
    self._source_ = source  ### TODO: modify to list of dataframes
    self._source_pandas_q = ''
    self.pre_gen_query = self.setup_query(q_gen_query)
    self.df_name = q_gen_query[0].df_name
    self.num_merges = 0
    self.operations = [  # not used
      'select',
      'merge',
      'order',
      'concat',
      'rename',
      'groupby',
    ]
    self.query_string = self.get_query_string()
    self.merged = False
    self.target = self.execute_query(self.pre_gen_query)  # target is the df after operation

    self.source_tables = [
      self.get_TBL_source()
    ]  # Initialize list of source tables for merged queries
    self.source_dataframes = [
      self.get_source()
    ]  # Initialize list of source dataframes for merged queries

  def can_do_merge(self):  # you can always do merge and groupby on df?
    """
    Placeholder for logic to determine if merging is possible.
    """
    pass

  def can_do_groupby(self):
    """
    Placeholder for logic to determine if grouping is possible.
    """
    pass

  def can_do_projection(self) -> bool:
    """
    Check if the DataFrame has any columns left for projection.

    :return: True if there are columns left, otherwise False.
    """
    if len(self.target.columns) > 0:
      return True

  def do_a_projection(self) -> Projection:
    """
    Create a projection operation with a random selection of columns.

    :return: A projection operation object.
    """
    columns = self.get_target().columns
    if len(columns) == 1:
      return [columns]

    else:
      # select random number of cols to project on
      res = [
        list(i) for i in list(itertools.combinations(columns, random.randrange(1, len(columns), 1)))
      ]
      random.shuffle(res)
      return Projection(self.df_name, res[0])

  def target_possible_selections(self, length=50) -> Dict[str, List[Condition]]:  # not used
    """
    Generate a dictionary of possible selection conditions based on numerical columns.

    :param length: The maximum number of conditions to generate for each column.
    :return: A dictionary mapping column names to lists of conditions.
    """
    # dictionary with col name as key and its data type as value
    possible_selection_columns = {}
    source_df = self.get_target()
    for i, col in enumerate(source_df.columns):
      # if first element of target df column is an int or float
      if 'int' in str(type(source_df[col][0])):
        possible_selection_columns[col] = 'int'
      elif 'float' in str(type(source_df[col][0])):
        possible_selection_columns[col] = 'float'

    # dict with col name as key and list of possible selection conditions as value
    possible_condition_columns = {}
    stats = ['min', 'max', 'count', 'mean', 'std', '25%', '50%', '75%']

    for key in possible_selection_columns:
      possible_condition_columns[key] = []
      # get stats for a given column
      description = self.get_source_description(source_df, key)

      # generate length=50 possible selection conditions for each column
      for i in range(length):
        if possible_selection_columns[key] == 'int':
          # add up to one std to randomly chosen statistic
          cur_val = round(description[random.choice(stats)]) + random.randrange(
            0, description['std'] + 1, 1
          )
        else:
          cur_val = float(
            description[random.choice(stats)] + random.randrange(0, description['std'] + 1, 1)
          )

        OPs = [Operator.gt, Operator.ge, Operator.le, Operator.eq, Operator.lt, Operator.ne]

        cur_condition = Condition(key, random.choice(OPs), cur_val)
        possible_condition_columns[key].append(cur_condition)
    return possible_condition_columns

  # difference with previous method?
  def possible_selections(self, length=50) -> Dict[str, List[Condition]]:
    """
    Generate a dictionary of possible selection conditions for each numerical column.

    :param length: The maximum number of conditions to generate for each column.
    :return: A dictionary mapping column names to lists of conditions.
    """
    possible_selection_columns = {}

    source_df = self.get_source()

    for i, col in enumerate(source_df.columns):
      # This checks if the dtype of the entire column is an integer type.
      if pd.api.types.is_integer_dtype(source_df[col]):
        possible_selection_columns[col] = 'int'
      elif pd.api.types.is_float_dtype(source_df[col]):
        possible_selection_columns[col] = 'float'
      elif (
        pd.api.types.is_string_dtype(source_df[col])
        and col in data_ranges[self.df_name]
        and not isinstance(data_ranges[self.df_name][col], list)
      ):
        # Check if the string column contains dates
        sample_value = source_df[col].iloc[0]
        try:
          pd.to_datetime(sample_value, format='%Y-%m-%d')
          possible_selection_columns[col] = 'date'
        except ValueError:
          possible_selection_columns[col] = 'string'
      # enum values are stored as lists in data_ranges
      elif col in data_ranges[self.df_name] and isinstance(data_ranges[self.df_name][col], list):
        possible_selection_columns[col] = 'enum'

    possible_condition_columns = {}

    for key in possible_selection_columns:
      possible_condition_columns[key] = []  # key: col name，value: condition object list
      for i in range(length):
        if possible_selection_columns[key] == 'int':
          min_val, max_val = data_ranges[self.df_name][
            key
          ]  # data_ranges dict initialized in __main__, stores data ranges of each column for df_name
          cur_val = random.randint(min_val, max_val)
          # Ensure no conditions are created with values out of range
          if min_val == max_val:
            op = Operator.eq
          elif cur_val == min_val:
            op = random.choice([Operator.gt, Operator.ge, Operator.eq, Operator.ne])
          elif cur_val == max_val:
            op = random.choice([Operator.lt, Operator.le, Operator.eq, Operator.ne])
          else:
            op = random.choice(
              [Operator.gt, Operator.ge, Operator.lt, Operator.le, Operator.eq, Operator.ne]
            )
          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'float':
          min_val, max_val = data_ranges[self.df_name][key]
          cur_val = round(random.uniform(min_val, max_val), 2)  # Assume 2 decimal places
          # Ensure no conditions are created with values out of range, no == or != operators for floats
          if min_val == max_val:
            op = Operator.eq
          elif cur_val == min_val:
            op = random.choice([Operator.gt, Operator.ge])
          elif cur_val == max_val:
            op = random.choice([Operator.lt, Operator.le])
          else:
            op = random.choice([Operator.gt, Operator.ge, Operator.lt, Operator.le])

          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'string':
          cur_val = random.choice(data_ranges[self.df_name][key][0])  # starting char
          cur_condition = Condition(key, Operator.startswith, cur_val)

        elif possible_selection_columns[key] == 'date':
          min_val, max_val = data_ranges[self.df_name][key]
          min_date = pd.to_datetime(min_val, format='%Y-%m-%d')
          max_date = pd.to_datetime(max_val, format='%Y-%m-%d')
          cur_val = pd.to_datetime(random.choice(pd.date_range(min_date, max_date))).strftime(
            '%Y-%m-%d'
          )
          if min_val == max_val:
            op = Operator.eq
          elif cur_val == min_val:
            op = random.choice([Operator.gt, Operator.ge])
          elif cur_val == max_val:
            op = random.choice([Operator.lt, Operator.le])
          else:
            op = random.choice([Operator.gt, Operator.ge, Operator.lt, Operator.le])
          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'enum':
          if random.choice([True, False]):  # Randomly choose between == and IN condition
            cur_val = f"'{random.choice(data_ranges[self.df_name][key])}'"
            op = random.choice([Operator.eq, Operator.ne])
            cur_condition = Condition(key, op, cur_val)
          else:
            num_in_values = random.randint(2, len(data_ranges[self.df_name][key]))
            in_values = [
              val for val in random.sample(data_ranges[self.df_name][key], num_in_values)
            ]
            cur_condition = Condition(key, Operator.in_op, in_values)

        possible_condition_columns[key].append(cur_condition)

    return possible_condition_columns

  def get_TBL_source(self) -> 'TableSource':
    """
    Get the source table object.

    :return: The source TBL_source object.
    """
    return self._source_

  def get_target(self) -> pd.DataFrame:
    """
    Get the resulting DataFrame after applying the query operations.

    :return: The resulting DataFrame.
    """
    return self.target

  def get_source(self) -> pd.DataFrame:
    """
    Get a copy of the source DataFrame.

    :return: A copy of the source DataFrame.
    """
    return self._source_.source.copy()

  def get_source_tables(self):
    """
    Get the source tables of a merged query.

    :return: The list of source tables.
    """
    return self.source_tables

  def get_source_dataframes(self):
    """
    Get the source dataframes of a merged query.

    :return: The list of source dataframes.
    """
    return self.source_dataframes

  def setup_query(self, list_op: List[Operation]) -> List[Operation]:
    """
    Test if the list of operations works for this query, and modify it to a working format if not.

    :param list_op: List of operations to validate.
    :return: A list of operations that function properly.
    for example: project col1 and col2, then can't do further selections on other colums
    """
    list_operation = list_op[:]
    source_cols = list(self.get_source().columns)  # get all existing columns
    changed = False
    # source_cols is the columns available after the projection
    for i, operation_ in enumerate(list_operation):
      if isinstance(operation_, Projection):
        source_cols = operation_.desire_columns[:]  # desire_col: col to be projected
        changed = True
      # group_by must only use columns available after projections
      elif isinstance(operation_, GroupBy):
        if isinstance(operation_, GroupBy) and changed:
          #     print("available columns changed!!!")
          for g_col in operation_.columns:
            if g_col not in source_cols:
              col = random.choice(source_cols)
              operation_.set_columns([col])
            # print(f"%%%%% source cols = {source_cols}, modified columns = {operation_.columns}")
      if i != 0:
        operation_.set_leading(False)
    return list_operation

  def gen_queries(self, params, maxrange=1000) -> List[List[Operation]]:
    """
    :param params: Dictionary storing user-defined query parameters
    :param maxrange: threshold for selection
    :return: Nested List of operation lists; an operation list can be directly transferred into a pandas query
    """
    generated_queries = []
    for operation in self.pre_gen_query:
      possible_new_operations = []  # expanded possible new operations for each category of original operation

      if isinstance(operation, Selection):
        possible_conditions_dict = (
          self.possible_selections()
        )  # return a condition dict, col name is key, list of conditions is value

        possible_selection_operations = []
        possible_selection_operationsSrting = []
        print('===== generating selection combinations =====')
        num_selections = params.get('num_selections', 3)
        for i in range(maxrange):
          while True:
            selection_length = random.randint(0, num_selections)
            cur_conditions = []
            cur_conditionsString = []
            and_count = 0  # count the number of & operators
            for j in range(selection_length):
              cur_key = random.choice(list(possible_conditions_dict.keys()))  # key is col name
              cur_condition = random.choice(
                possible_conditions_dict[cur_key]
              )  # cur_condition is list of conditions

              if cur_condition.op != Operator.startswith:  # int or float col
                cur_conditions.append(cur_condition)
                if and_count < 2:
                  cur_conditions.append(
                    random.choice([ConditionalOperator.OR, ConditionalOperator.AND])
                  )
                  if cur_conditions[-1] == ConditionalOperator.AND:
                    and_count += 1
                else:
                  cur_conditions.append(ConditionalOperator.OR)
              else:
                cur_conditionsString.append(cur_condition)
                if and_count < 2:
                  cur_conditionsString.append(
                    random.choice([ConditionalOperator.OR, ConditionalOperator.AND])
                  )
                  if cur_conditionsString[-1] == ConditionalOperator.AND:
                    and_count += 1
                else:
                  cur_conditionsString.append(ConditionalOperator.OR)

            cur_conditions = cur_conditions[:-1]
            cur_conditionsString = cur_conditionsString[:-1]
            # check for logical consistency of cur_conditions
            new_selection = Selection(self.df_name, cur_conditions)
            new_selection_string = Selection(self.df_name, cur_conditionsString)
            if (
              new_selection.is_logically_consistent()
              and new_selection_string.is_logically_consistent()
            ):
              break
            else:
              continue

          possible_selection_operations.append(
            cur_conditions
          )  # nested list [[<__main__.condition object at 0x1193dead0>, <OP_cond.OR: '|'>, <__main__.condition object at 0x1193df650>]]
          possible_selection_operationsSrting.append(cur_conditionsString)

        # Create a list that includes both lists of operations
        options = [
          possible_selection_operations,
          possible_selection_operationsSrting,
        ]
        # Randomly choose one of the lists (either the list containing string operations or numerical operations)
        chosen_operations = random.choice(options)

        for conds in chosen_operations:
          possible_new_operations.append(operation.new_selection(conds))

      elif isinstance(operation, Projection):
        new_operations = self.generate_possible_column_combinations(operation)

        for ops in new_operations:
          possible_new_operations.append(operation.new_projection(ops))

      generated_queries.append(possible_new_operations)
      print('===== possible operations generated =====')

    new_generated_queries = []
    new_generated_queries = itertools.product(*generated_queries)  # op1.1*op2.3*op3.2

    print('======= *** start iterating generated queries *** ======')
    l = [item for item in new_generated_queries]

    print(' *** done ***')
    return l

  def get_new_pandas_queries(self, params, out=100) -> List['Query']:
    """
    Generate new pandas queries based on the existing operations.

    :param params: Dictionary storing user-defined query parameters.
    :param out: Maximum number of queries to generate.
    :return: List of pandas_query objects.
    """
    res = []  # stores pandas query objects generated
    new_queries = self.gen_queries(
      params
    )  # list of tuples, each tuple contains a combination of query operations

    random.shuffle(new_queries)  # Shuffle to avoid bias towards conditions of the first column
    new_queries = new_queries[:out]

    print(f' ==== Testing source with {len(new_queries)} queries ==== ')
    df = self.get_source()  # Assuming this gets a pandas DataFrame
    tbl = (
      self.get_TBL_source()
    )  # Assuming this gets some source necessary for query object creation
    progress_interval = max(1, len(new_queries) // 10)  # Ensure no division by zero

    for i, new_query in enumerate(new_queries):
      if i % progress_interval == 0:
        print(
          f'=== {i // progress_interval * 10}% ==='
        )  # for every 10%, indicates current % of new queries generated

      # Assume execute_query() is a method that takes a query and executes it against the DataFrame
      try:
        result_df = self.execute_query(new_query)  # Execute and get result
        new_q_obj = Query(
          new_query, tbl
        )  # create pandas_query object for each query executed on source tbl

        res.append(new_q_obj)
      except Exception as e:
        continue

    random.shuffle(res)  # shuffle result to ensure diverse order of queries
    print(f' ======= {len(res)} new queries generated =======')
    return res  # returns list of pandas query objects

  def check_res(self, res: List['Query']):
    """
    Check if the queries are in good grammar.

    :param res: List of pandas_query objects.
    :return: True
    """
    true_count = 0
    false_count = 0
    for r in res:
      try:
        df = eval(r.query_string)
      except Exception:
        false_count += 1
        continue
      true_count += 1
    print(f'%%%%%%%%%% truecount = {true_count}; false count = {false_count} %%%%%%%%%%%%')
    return True

  def execute_query(self, query) -> pd.DataFrame:
    """
    Execute the provided query operations.

    :param query: List of operations to execute. (why not used?)
    :return: Resulting DataFrame after applying the operations.
    """
    # Ensure 'query' is a DataFrame here; the exact implementation may vary.
    # 'query_string' should be a string that represents a pandas operation.
    query_string = self.get_query_string()  # Ensure this returns a safe, valid pandas expression.
    local_dict = {
      'dataframes': dataframes,
      'data_ranges': data_ranges,
      'foreign_keys': foreign_keys,
      'tbl_sources': table_sources,  # tbl_source = wrapper class for df with its foreign keys
    }
    return pd.eval(query_string, local_dict=local_dict)
    """try:
            # Assuming get_query_string() validates and sanitizes the input query string
            query_string = self.get_query_string()

            # Local dictionary defining the context for pd.eval()
            local_dict = {
                'dataframes': dataframes,
                'data_ranges': data_ranges,
                'foreign_keys': foreign_keys,
                'tbl_sources': tbl_sources
            }

            # Evaluate the query string in the context of local_dict
            result = pd.eval(query_string, local_dict=local_dict)
            if not isinstance(result, pd.DataFrame):
                result = pd.DataFrame([result])  # Convert Series or scalar to DataFrame

            return result
        except Exception as e:
            raise ValueError(f"Failed to execute query due to: {e}")"""

  # helper functions for gen_queries
  def generate_possible_groupby_combinations(self, operation: GroupBy, generate_num=5) -> List[str]:
    """
    Generate possible combinations of columns for groupby operations.

    :param operation: A group_by operation.
    :param generate_num: Maximum number of combinations to generate.
    :return: List of column names to group by.
    """
    print('===== generating groupby combinations =====')
    columns = self.get_source().columns
    possible_groupby_columns = []
    for col in columns:
      possible_groupby_columns.append(col)
    random.shuffle(possible_groupby_columns)
    return possible_groupby_columns[:generate_num]

  def generate_possible_agg_combinations(
    self, operation: Aggregate, generate_num=5
  ) -> List[Union[str, Dict[str, str]]]:
    """
    Generate possible combinations of aggregation functions.

    :param operation: An agg operation.
    :param generate_num: Maximum number of combinations to generate.
    :return: List of possible aggregation dictionaries or strings.
    """
    stats = ['min', 'max', 'count', 'mean']

    possible_dicts = []

    cur_dict = operation.dict_key_vals

    print('===== generating agg combinations =====')

    if isinstance(cur_dict, str):
      return stats

  def generate_possible_column_combinations(
    self, operation: Projection, generate_num=50
  ) -> List[List[str]]:
    """
    Generate possible combinations of columns for projection operations.

    :param operation: A projection operation.
    :param generate_num: Maximum number of combinations to generate.
    :return: List of lists of column combinations.
    """
    columns = self.get_source().columns
    possible_columns = []

    print('===== generating column combinations =====')

    if len(columns) == 1:
      return [columns]

    else:
      res = []
      for length in range(1, len(columns) + 1):
        res += [list(i) for i in list(itertools.combinations(columns, length))]
      """
            res = [list(i) for i in
                   list(itertools.combinations(columns, operation.length))]
            if operation.length > 1 and operation.length < len(list(columns)):
                res = res + [list(i) for i in list(itertools.combinations(columns, operation.length - 1))]
                res = res + [list(i) for i in list(itertools.combinations(columns, operation.length + 1))]
            """
      random.shuffle(res)
      return res[:generate_num]

  def generate_possible_selection_operations(
    self, possible_new_conditions, generate_num=100
  ) -> List[List[Union[Condition, ConditionalOperator]]]:
    """
    Generate possible combinations of selection conditions.

    :param possible_new_conditions: List of conditions and logical operators.
    :param generate_num: Maximum number of combinations to generate.
    :return: List of lists, each containing a combination of conditions and logical operators.
    """
    print('===== generating selection combinations =====')
    new_conds = []  # holds all the generated combinations
    clocks = (
      [0] * len(possible_new_conditions)
    )  # list of zero-initialized counters to keep track of the progress of conditions for each column.

    for c in range(generate_num):
      possible_cond = []  # stores individual selection conditions for each combination
      for i, new_cond in enumerate(possible_new_conditions):
        if isinstance(new_cond, ConditionalOperator):
          # Limit number of & operators to 2 in each seleciton
          if new_cond == ConditionalOperator.AND:
            if and_count >= 2:
              continue
            else:
              and_count += 1
          cur = random.choice([ConditionalOperator.OR, ConditionalOperator.AND])
          possible_cond.append(cur)
          continue
        if clocks[i] < len(new_cond):  # what does clocks[i] do?
          possible_new_ith_condition = new_cond[clocks[i]]
          clocks[i] += 1
        else:
          clocks[i] = 0
          possible_new_ith_condition = new_cond[clocks[i]]

        # Ensure only valid conditions for floats
        if (
          possible_new_ith_condition.op in [Operator.eq, Operator.ne]
          and possible_new_ith_condition.val == float
        ):
          continue

        possible_cond.append(possible_new_ith_condition)
      # Only add logically consistent conditions
      new_selection_op = Selection(self.df_name, possible_cond)
      if new_selection_op.is_logically_consistent():
        new_conds.append(possible_cond)

    random.shuffle(new_conds)
    return new_conds[:generate_num]

  def get_possible_values(self, col):
    """
    Get descriptive statistics of a given column.

    :param col: The column name.
    :return: Descriptive statistics of the column.
    """
    des = self.get_source_description(self.get_source(), col)
    return des

  def get_query_string(self) -> str:
    """
    Generate a string representation of the entire query.

    :return: A string representing the query operations.
    """
    strs = ''
    for q in self.pre_gen_query:
      strs += q.to_str()

    return strs

  # get descriptive statistics of a given col
  def get_source_description(self, dfa: pd.DataFrame, col) -> pd.Series:
    """
    Get the descriptive statistics of a given column in the DataFrame.

    :param dfa: The DataFrame to describe.
    :param col: The column name.
    :return: Descriptive statistics of the column.
    """
    des = dfa.describe()

    return des[col]

  # What is this method used for?
  def to_pandas_template(self):
    cur = ''


class QueryPool:
  result_queries: list[Any]

  """
    Class for managing and processing a pool of pandas queries, including generating merged queries.

    Attributes:
        queries (List[pandas_query]): List of queries of type pandas_query.
        count (int): Counter for generating DataFrame names during merging.
        self_join (bool): Whether tables can be joined with themselves.
        verbose (bool): Whether to print the processing steps.
        result_queries (List[pandas_query]): List to store the merged queries.
        un_merged_queries (List[pandas_query]): List of queries that haven't been merged.
    """

  def __init__(self, queries: List[Query], count=0, self_join=False, verbose=True):
    """
    Initialize a QueryPool object.

    :param queries: List of queries in type pandas_query.
    :param count: Counter for generating DataFrame names.
    :param self_join: Whether to allow self-joins.
    :param verbose: Whether to print the processing steps.
    """
    self.count = count
    self.queries = queries  # Can be shuffled and manipulated independantly
    self.result_queries = []
    self.self_join = self_join
    self.un_merged_queries = queries[
      :
    ]  # Stores a copy of the original queries to generate unmerged examples
    self.verbose = verbose

  def save_merged_examples(self, directory: str, filename: str) -> None:
    """
    Save the merged queries into a text file if the content has changed.

    :param directory: Directory path where the file should be saved.
    :param filename: Name of the file to save.
    """
    filepath = Path(directory) / f'{filename}.txt'

    # Create directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Generate new content
    new_content = '\n'.join(f'df{i} = {q.query_string}' for i, q in enumerate(self.result_queries))

    # Write new content
    with open(filepath, 'w') as f:
      f.write(new_content)

    print(f'Successfully wrote the merged queries into file {filepath}')

  def save_merged_examples_multiline(self, directory: str, filename: str) -> None:
    count = 0
    try:
      f = open(f'{directory}/{filename}.txt', 'a')
    except:
      filepath = f'{directory}/{filename}.txt'
      os.makedirs(os.path.dirname(filepath), exist_ok=True)
      f = open(f'{directory}/{filename}.txt', 'a')
    res = {}
    q = []
    exception_count = [0]

    def unravel(query: Query, exception_count):
      wstrs = query.pre_gen_query
      numOP = len(wstrs)
      step = 0
      try:
        p = eval(wstrs)
      except Exception:
        # f.write("Next \n")
        exception_count[0] += 1
        # pass

      for s in query.pre_gen_query:
        strs = s.to_str()
        if isinstance(s, Merge):
          counter = self.count - 1

          # b = max(unravel(other))
          unravel(s.queries, exception_count)

          f.write(
            f'df{self.count} = df{counter}.merge(df{self.count - 1}, left_on={s.left_on}, right_on={s.right_on}) \n'
          )
          self.count += 1
          continue

        if s.leading:
          s1 = s.to_str()
          f.write(f'df{self.count} = {s1} \n')  # strs
        else:
          if isinstance(s, Selection):
            s2 = s.to_str(str(self.count - 1))
          else:
            s2 = s.to_str()
          f.write(f'df{self.count} = df{self.count - 1}' + s2 + '\n')
        step += 1
        self.count += 1

    for m in self.result_queries:
      count = unravel(m, exception_count)
      f.write('Next \n')

    print(
      f' ##### Successfully write the merged queries into file {directory}/{filename}.txt #####'
    )
    f.close()

  def shuffle_queries(self):
    """
    Shuffle the order of queries in the pool.
    """
    random.shuffle(self.queries)

  def ranges_overlap(self, range1, range2):
    """
    Check if two ranges overlap.

    :param range1: A tuple representing the range (min, max) of the first column.
    :param range2: A tuple representing the range (min, max) of the second column.
    :return: True if the ranges overlap, otherwise False.
    """
    min1, max1 = range1
    min2, max2 = range2
    return max(min1, min2) <= min(max1, max2)

  def check_merge_on(self, q1: Query, q2: Query):
    """
    Return a list of common columns between two queries for merging.

    :param q1: First query of type pandas_query.
    :param q2: Second query of type pandas_query.
    :return: List of column names that can be used for merging.
    """
    if 'series' in str(type(q1.get_target())) or 'series' in str(type(q2.get_target())):
      return []
    cols = q1.get_target().columns.intersection(q2.get_target().columns)
    if len(cols) == 0 or len(cols) == min(
      len(q1.get_source().columns), len(q2.get_source().columns)
    ):
      return None

    # Filter out columns with non-overlapping ranges
    valid_cols = []
    for col in cols:
      range1 = data_ranges[q1.df_name].get(col, None)
      range2 = data_ranges[q2.df_name].get(col, None)
      if range1 and range2:
        # Check if column types are int or float
        if pd.api.types.is_integer_dtype(q1.get_source()[col]) or pd.api.types.is_float_dtype(
          q1.get_source()[col]
        ):
          if pd.api.types.is_integer_dtype(q2.get_source()[col]) or pd.api.types.is_float_dtype(
            q2.get_source()[col]
          ):
            if self.ranges_overlap(range1, range2):
              valid_cols.append(col)

    return valid_cols if valid_cols else None

  def check_merge_left_right(self, q1: Query, q2: Query):
    """
    Return a list of columns to merge two DataFrames based on foreign key relationships.

    :param q1: First query of type pandas_query.
    :param q2: Second query of type pandas_query.
    :return: List of two column names if a relationship is found, otherwise an empty list.
    """

    if isinstance(q1.get_target(), Series) or isinstance(q2.get_target(), Series):
      return []

    col1 = list(q1.get_target().columns)
    col2 = list(q2.get_target().columns)

    q1_foreign_keys = q1.get_TBL_source().get_foreign_keys()
    q2_foreign_keys = q2.get_TBL_source().get_foreign_keys()

    foreign_list = {}
    for key in q1_foreign_keys:
      if key in col1:
        for a in q1_foreign_keys[key]:
          foreign_list[a[0]] = key

    for col in col2:
      if col in foreign_list:
        range1 = data_ranges[q1.df_name].get(foreign_list[col], None)
        range2 = data_ranges[q2.df_name].get(col, None)
        if range1 and range2:
          # Check if column types are int or float
          if pd.api.types.is_integer_dtype(
            q1.get_source()[foreign_list[col]]
          ) or pd.api.types.is_float_dtype(q1.get_source()[foreign_list[col]]):
            if pd.api.types.is_integer_dtype(q2.get_source()[col]) or pd.api.types.is_float_dtype(
              q2.get_source()[col]
            ):
              if self.ranges_overlap(range1, range2):
                return [foreign_list[col], col]

    return []

  # TODO: function currently merges all unmerged queries in cur_queries first and only once there are no more unmerged queries, it uses the merged queries that it generated
  # TODO: this function should be modified to merge queries in a more balanced way (first use all unmerged queries to generate new queries with one or two merges, shuffle the queries in cur_queries, then merge them)

  def generate_possible_merge_operations(self, params, max_merge=3, max_q=5000):
    cur_queries = self.queries[:]
    random.shuffle(cur_queries)

    categorized_queries = defaultdict(list)
    categorized_queries[0] = self.un_merged_queries[:]
    random.shuffle(categorized_queries[0])

    # dictionary to store merged queries with groupby and aggregation
    merged_queries_groupby_agg = defaultdict(list)

    # add max_q/(max_merge+1) unmerged queries to the result
    unmerged_query_count = 0

    stats = ['min', 'max', 'count', 'mean']

    # add groupby and aggregation operations to the unmerged queries
    for query in categorized_queries[0]:
      if unmerged_query_count >= max_q // (max_merge + 1):
        break

      operations = list(query.pre_gen_query)[:]
      strs = ''
      for op in operations:
        # print("cur op = " + str(op))
        strs += op.to_str()

        # print("cur op to str = " + op.to_str())
      # print(f"strs here = {strs}")

      if self.verbose:
        print(f'strs here = {strs}')
      try:
        t = eval(strs)
        if t.shape[0] == 0:
          if self.verbose:
            print('no rows exist with the above selection')
          continue
      except Exception:
        continue

      if (
        random.random() > 0.5
        and params.get('group by', 'True') == 'True'
        and params.get('aggregation', 'True') == 'True'
      ):
        operations = list(query.pre_gen_query)[:]
        operations_with_groupby_agg = operations[:]

        groupby_column = query.generate_possible_groupby_combinations(
          GroupBy(query.df_name, query.get_source().columns), generate_num=1
        )

        operations_with_groupby_agg.append(GroupBy(query.df_name, groupby_column))
        operations_with_groupby_agg.append(Aggregate(query.df_name, random.choice(stats)))

        new_query_with_groupby_agg = Query(
          operations_with_groupby_agg, query.get_TBL_source(), verbose=False
        )
        self.result_queries.append(new_query_with_groupby_agg)

      elif (
        random.random() > 0.5
        and params.get('group by', 'True') == 'False'
        and params.get('aggregation', 'True') == 'True'
      ):
        operations = list(query.pre_gen_query)[:]
        operations_with_agg = operations[:]

        operations_with_agg.append(Aggregate(query.df_name, random.choice(stats)))

        new_query_with_agg = Query(operations_with_agg, query.get_TBL_source(), verbose=False)
        self.result_queries.append(new_query_with_agg)

      else:
        self.result_queries.append(query)

      unmerged_query_count += 1

    k = 0  # counter for number of merges
    res_hash = {}
    q_generated = 0
    while True:
      if k >= max_merge:
        break

      for i in tqdm(range(len(categorized_queries[0]) - 1)):
        for j in range(len(categorized_queries[k])):
          if q_generated >= 2 * (k + 1) * (max_q // (max_merge + 1)):
            break

          if str(i) + '+' + str(j) not in res_hash:
            # randomly select queries to ensure a more equal distribution of source tables
            q1_index = random.randint(0, len(categorized_queries[0]) - 1)
            # ensure that q1 and q2 are different
            while True:
              q2_index = random.randint(0, len(categorized_queries[k]) - 1)
              if q1_index != q2_index:
                break
            q1 = categorized_queries[0][q1_index]  # first query (unmerged)
            q2 = categorized_queries[k][q2_index]  # second query (merged with k merges)

            # print(f"q1 df name = {q1}")
            # print(f"q2 df_name = {q2}")

            if any(
              q2_source.equals(q1.get_source()) for q2_source in q2.get_source_dataframes()
            ) and (not self.self_join):
              # print("#### queries with same source detected, skipping to the next queries ####")
              continue

            merge_differenet_keys = self.check_merge_left_right(q1, q2)

            if len(merge_differenet_keys) > 0:
              if self.verbose:
                print(f'keys to merge = {merge_differenet_keys}')
              operations = list(q1.pre_gen_query)[:]

              operations.append(
                Merge(
                  df_name=q1.df_name,
                  queries=q2,
                  left_on=merge_differenet_keys[0],
                  right_on=merge_differenet_keys[1],
                )
              )

              strs = ''

              for op in operations:
                # print("cur op = " + str(op))
                strs += op.to_str()

                # print("cur op to str = " + op.to_str())
              # print(f"strs here = {strs}")

              if self.verbose:
                print(f'strs here = {strs}')
              try:
                t = eval(strs)
                if t.shape[0] == 0:
                  if self.verbose:
                    print('no rows exist with the above selection')
                  continue
              except Exception:
                continue
              else:
                if self.verbose:
                  print('successfully generated query')
              try:
                res_df = q1.get_target().merge(
                  q2.get_target(),
                  left_on=merge_differenet_keys[0],
                  right_on=merge_differenet_keys[1],
                )

                columns = list(t.columns)
                rand = random.random()

                # Add a projection operation to the merged query
                if rand > 0.5 and len(columns) and params.get('projection', 'True') == 'True':
                  num = random.randint(max(len(columns) - 2, 3), len(columns))
                  sample_columns = random.sample(columns, num)
                  operations.append(Projection(q1.df_name, sample_columns))
                  res_df.columns = sample_columns

              except Exception:
                if self.verbose:
                  print('Exception occurred')
                continue
              if self.verbose:
                print('++++++++++ add the result query to template +++++++++++++')
              new_query = Query(operations, q1.get_TBL_source(), verbose=False)

              new_query.target = res_df
              new_query.num_merges = max(q1.num_merges, q2.num_merges) + 1

              # Add the source tables of q2 to the new query
              new_query.source_tables.extend(q2.get_source_tables())
              new_query.source_dataframes.extend(q2.get_source_dataframes())

              # Append the query with groupby and agg to result queries, and the query without groupby and agg to categorized_queries
              if new_query.num_merges == k + 1:
                cur_queries.append(new_query)
                categorized_queries[k + 1].append(new_query)
                res_hash[f'{str(i)}+{str(j)}'] = 0

                # Create a copy of operations for the query with groupby and agg
                operations_with_groupby_agg = operations[:]

                # Add group_by and agg operations only if columns are available
                if (
                  random.random() > 0.5
                  and params.get('group by', 'True') == 'True'
                  and params.get('aggregation', 'True') == 'True'
                ):
                  target_columns = list(new_query.get_target().columns)
                  group_by_column = random.choice(target_columns)

                  # Check which table the groupby column belongs to
                  for table in new_query.get_source_tables():
                    if group_by_column in table.source.columns:
                      df_name = table.name
                      break

                  stats = ['min', 'max', 'count', 'mean']
                  operations_with_groupby_agg.append(GroupBy(df_name, group_by_column))
                  operations_with_groupby_agg.append(Aggregate(df_name, random.choice(stats)))

                  new_query_with_groupby_agg = Query(
                    operations_with_groupby_agg,
                    q1.get_TBL_source(),
                    verbose=False,
                  )
                  new_query_with_groupby_agg.target = res_df
                  new_query_with_groupby_agg.num_merges = new_query.num_merges
                  new_query_with_groupby_agg.source_tables.extend(q2.get_source_tables())

                  merged_queries_groupby_agg[k + 1].append(new_query_with_groupby_agg)
                  # self.result_queries.append(new_query_with_groupby_agg)
                  q_generated += 1

                elif (
                  random.random() > 0.5
                  and params.get('group by', 'True') == 'False'
                  and params.get('aggregation', 'True') == 'True'
                ):
                  operations_with_groupby_agg.append(Aggregate(df_name, random.choice(stats)))

                  new_query_with_agg = Query(
                    operations_with_groupby_agg,
                    q1.get_TBL_source(),
                    verbose=False,
                  )
                  new_query_with_agg.target = res_df
                  new_query_with_agg.num_merges = new_query.num_merges
                  new_query_with_agg.source_tables.extend(q2.get_source_tables())

                  merged_queries_groupby_agg[k + 1].append(new_query_with_groupby_agg)
                  # self.result_queries.append(new_query_with_agg)
                  q_generated += 1

                else:
                  q_generated += 1
                  merged_queries_groupby_agg[k + 1].append(new_query)
                  # self.result_queries.append(new_query)

                if q_generated % 1000 == 0:
                  print(f'**** {q_generated} queries have generated ****')

            else:
              ###################################################
              cols = self.check_merge_on(q1, q2)

              if cols and max(q1.num_merges, q2.num_merges) < max_merge and self.self_join:
                # print(cols)
                operations = list(q1.pre_gen_query)[:]

                operations.append(Merge(df_name=q1.df_name, queries=q2, on=cols))

                strs = ''

                for op in operations:
                  # print("cur op = " + str(op))
                  strs += op.to_str()

                  # print("cur op to str = " + op.to_str())
                if self.verbose:
                  print(f'strs here = {strs}')
                t = eval(strs)

                if t.shape[0] == 0:
                  if self.verbose:
                    print('no rows exist with the above selection')
                  continue

                else:
                  if self.verbose:
                    print('successfully generated query')
                try:
                  res_df = q1.get_target().merge(q2.get_target(), on=cols)

                except Exception:
                  if self.verbose:
                    print('Exception occurred')
                  continue
                if self.verbose:
                  print('++++++++++ add the result query to template +++++++++++++')

                new_query = Query(operations, q1.get_TBL_source(), verbose=False)
                new_query.merged = True
                new_query.target = res_df
                new_query.num_merges = max(q1.num_merges, q2.num_merges) + 1

                # Add the source tables of q2 to the new query
                new_query.source_tables.extend(q2.get_source_tables())

                if new_query.num_merges == k + 1:  # Check if number of merges exceeds max_merge
                  cur_queries.append(new_query)
                  categorized_queries[k + 1].append(new_query)
                  self.result_queries.append(new_query)
                  res_hash[f'{str(i)}+{str(j)}'] = 0

                  q_generated += 1

                  if q_generated % 1000 == 0:
                    print(f'**** {q_generated} queries have generated ****')

      k += 1

    # sample merged queries for each number of merges
    for i in range(1, max_merge + 1):
      if len(categorized_queries[i]) > 0:
        self.result_queries.extend(
          random.sample(
            merged_queries_groupby_agg[i],
            min(len(merged_queries_groupby_agg[i]), max_q // (max_merge + 1)),
          )
        )

    return cur_queries


class TableSource:
  """
  The primary source that reads from the csv / accessible file, a wrapper of the pd.DataFrame class
  """

  def __init__(self, df: pd.DataFrame, name):
    """

    :param df: pd.dataframe
    :param name: referring to the name of the dataframe
    :param foreign_keys: a hashmap that records all the foreign key pairs
    """
    self.source = df
    self.foreign_keys = {}
    self.name = name

  def get_numerical_columns(self):
    """
    :return: the column names that are type int / float
    """

    numerical_df = self.source.select_dtypes(include=['int64', 'float64'])
    num_columns = numerical_df.columns.tolist()
    return num_columns

  def get_a_selection(self):
    """
    perform a random selection on the dataframe
    :return: an object of type selection
    """
    possible_selection_columns = self.source.columns.tolist()
    if not possible_selection_columns:
      raise ValueError('No suitable numerical columns available for selection.')
    choice_col = random.choice(possible_selection_columns)

    if self.source[choice_col].dtype.kind in 'if':  # Check if the column is float or int
      min_val, max_val = data_ranges[entity][choice_col]
      num = random.uniform(min_val, max_val)
      if self.source[choice_col].dtype.kind == 'i':  # If it's an int, round it
        num = round(num)

    if self.source[choice_col].dtype.kind == 'i':
      if min_val == max_val:
        op_choice = Operator.eq
      elif num == min_val:
        op_choice = random.choice([Operator.gt, Operator.ge, Operator.eq, Operator.ne])
      elif num == max_val:
        op_choice = random.choice([Operator.lt, Operator.le, Operator.eq, Operator.ne])
      else:
        op_choice = random.choice(
          [Operator.gt, Operator.ge, Operator.lt, Operator.le, Operator.eq, Operator.ne]
        )

    elif self.source[choice_col].dtype.kind == 'f':
      if min_val == max_val:
        op_choice = Operator.eq
      elif num == min_val:
        op_choice = random.choice([Operator.gt, Operator.ge])
      elif num == max_val:
        op_choice = random.choice([Operator.lt, Operator.le])
      else:
        op_choice = random.choice([Operator.gt, Operator.ge, Operator.lt, Operator.le])

    elif (
      self.source[choice_col].dtype == 'object' or self.source[choice_col].dtype == 'string'
    ) and not isinstance(data_ranges[self.name][choice_col], list):
      # Check if the string column contains dates
      sample_value = self.source[choice_col].iloc[0]
      try:
        pd.to_datetime(sample_value, format='%Y-%m-%d')
        min_val, max_val = data_ranges[self.name][choice_col]
        min_date = pd.to_datetime(min_val, format='%Y-%m-%d')
        max_date = pd.to_datetime(max_val, format='%Y-%m-%d')
        num = pd.to_datetime(random.choice(pd.date_range(min_date, max_date))).strftime('%Y-%m-%d')
        if min_date == max_date:
          op_choice = Operator.eq
        elif num == min_date:
          op_choice = random.choice([Operator.gt, Operator.ge])
        elif num == max_date:
          op_choice = random.choice([Operator.lt, Operator.le])
        else:
          op_choice = random.choice([Operator.gt, Operator.ge, Operator.lt, Operator.le])
      except ValueError:
        startL = data_ranges[self.name][choice_col][0]
        num = random.choice(startL)  # starting char
        op_choice = Operator.startswith

    # enum values are stored in lists in data ranges
    elif (
      self.source[choice_col].dtype == 'object' or self.source[choice_col].dtype == 'string'
    ) and isinstance(data_ranges[self.name][choice_col], list):
      if random.choice([True, False]):
        num = f"'{random.choice(data_ranges[self.name][choice_col])}'"
        op_choice = random.choice([Operator.eq, Operator.ne])
      else:
        num_in_values = random.randint(2, len(data_ranges[self.name][choice_col]))
        in_values = [
          val for val in random.sample(data_ranges[self.name][choice_col], num_in_values)
        ]
        op_choice = Operator.in_op
        num = in_values

    cur_condition = Condition(
      choice_col, op_choice, num
    )  # don't need to check consistency since only one condition
    return Selection(self.name, [cur_condition])

  def get_a_projection(self):
    """
    perform a random projection on the dataframe
    :return: an object of type projection
    """
    columns = self.source.columns
    # Ensure 'num' is within the valid range
    max_num = len(columns)  # Maximum 'num' can be the length of 'columns'
    min_num = 1  # Minimum 'num' should be 1 to avoid a negative or zero value

    # Adjust 'num' to not exceed the number of available columns
    num = min(random.randint(max(min_num, 1), max(max_num, 1)), len(columns))

    # num = random.randint(max(len(columns) - 2, 3), len(columns))
    res_col = random.sample(list(columns), num)
    return Projection(self.name, res_col)

  def get_a_aggregation(self):
    """
    perform a random agg on the dataframe
    :return: an object of type aggregation
    """
    stats = ['min', 'max', 'count', 'mean']
    return Aggregate(self.name, random.choice(stats))

  def get_a_groupby(self):
    columns = self.source.columns
    res_col = [random.choice(list(columns))]  # selects a single column from columns list
    return GroupBy(self.name, res_col)

  def add_edge(self, col_name, other_col_name, other: 'TableSource'):
    """

    :param col_name: key on the current dataframe
    :param other_col_name: key on the foreign dataframe
    :param other: the other dataframe
    :return: void
    """
    # add a foreign key constraint between self and other df
    self.foreign_keys[col_name] = []
    self.foreign_keys[col_name].append([other_col_name, other])

  def get_foreign_keys(self):
    """
    :return: get all foreign keys
    """
    return self.foreign_keys.copy()

  def equals(self, o: 'TableSource'):
    return self.source.equals(o.source)

  def gen_base_queries(self, params) -> List[Query]:
    """
    Customized generation with base queries, can be modified to fit in various circumstances
    param query_types: types of queries specified by the user
    :return: List[pandas_query]
    """

    q_gen_query_1 = []
    q_gen_query_2 = []
    q_gen_query_3 = []
    q_gen_query_4 = []

    if params.get('num_selections', 3) > 0 and params.get('projection', 'True') == 'True':
      q_gen_query_1.append(self.get_a_projection())
      q_gen_query_2.append(self.get_a_selection())
      q_gen_query_3.append(self.get_a_selection())
      q_gen_query_3.append(self.get_a_projection())
      q_gen_query_4.append(self.get_a_selection())

    elif params.get('num_selections', 3) == 0 and params.get('projection', 'True') == 'True':
      q_gen_query_1.append(self.get_a_projection())
      q_gen_query_2.append(self.get_a_projection())
      q_gen_query_3.append(self.get_a_projection())
      q_gen_query_4.append(self.get_a_projection())

    elif params.get('num_selections', 3) > 0 and params.get('projection', 'True') == 'False':
      q_gen_query_1.append(self.get_a_selection())
      q_gen_query_2.append(self.get_a_selection())
      q_gen_query_3.append(self.get_a_selection())
      q_gen_query_4.append(self.get_a_selection())

    else:
      sys.exit(
        'Invalid parameters for generating base queries. Must have at least one selection or projection operation.'
      )

    q1 = Query(q_gen_query=q_gen_query_1, source=self)
    q2 = Query(q_gen_query=q_gen_query_2, source=self)
    q3 = Query(q_gen_query=q_gen_query_3, source=self)
    q4 = Query(q_gen_query=q_gen_query_4, source=self)

    queries = [q1, q2, q3, q4]

    return queries


# This is just testing for TPC-H from previous model
def test_patients():
  """
  Please use Main to run this script, this is just an example of workflow
  :return:
  """
  df = pd.read_csv('./patient_ma_bn.csv')
  q1 = [
    Selection(
      'df',
      conditions=[
        Condition('Age', Operator.gt, 50),
        ConditionalOperator.OR,
        Condition('Age', Operator.le, 70),
      ],
    ),
    Projection('df', ['Age', 'Sex', 'operation', 'P1200', 'P1600', 'Smoking']),
    GroupBy('df', 'Sex'),
    Aggregate('df', 'min'),
  ]
  q2 = [
    Selection(
      'df',
      conditions=[
        Condition('Age', Operator.gt, 50),
        ConditionalOperator.AND,
        Condition('Height', Operator.le, 160),
        ConditionalOperator.AND,
        Condition('TNM_distribution', Operator.eq, 1),
      ],
    ),
    Projection('df', ['Age', 'Sex', 'P1210', 'P100', 'Smoking', 'Weight']),
    GroupBy('df', 'Smoking'),
    Aggregate('df', 'count'),
  ]
  pq1 = Query(q1, source=df)
  pq2 = Query(q2, source=df)

  res = pq1.get_new_pandas_queries()[:1000] + pq2.get_new_pandas_queries()[:1000]

  queries = QueryPool(res)
  queries.generate_possible_merge_operations(3)


def run_TPCH():
  customer = TableSource(pd.read_csv('./../../../benchmarks/customer.csv'), 'customer')
  lineitem = TableSource(pd.read_csv('./../../../benchmarks/lineitem.csv'), 'lineitem')
  nation = TableSource(pd.read_csv('./../../../benchmarks/nation.csv'), 'nation')
  orders = TableSource(pd.read_csv('./../../../benchmarks/orders.csv'), 'orders')
  part = TableSource(pd.read_csv('./../../../benchmarks/part.csv'), 'part')
  partsupp = TableSource(pd.read_csv('./../../../benchmarks/partsupp.csv'), 'partsupp')
  region = TableSource(pd.read_csv('./../../../benchmarks/region.csv'), 'region')
  supplier = TableSource(pd.read_csv('./../../../benchmarks/supplier.csv'), 'supplier')

  q1 = [
    Selection(
      'customer',
      conditions=[
        Condition('ACCTBAL', Operator.gt, 100),
        ConditionalOperator.OR,
        Condition('CUSTKEY', Operator.le, 70),
      ],
    ),
    Projection('customer', ['CUSTKEY', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'MKTSEGMENT']),
  ]
  q2 = [
    Selection(
      'customer',
      conditions=[
        Condition('ACCTBAL', Operator.gt, 100),
        ConditionalOperator.OR,
        Condition('CUSTKEY', Operator.le, 70),
      ],
    ),
    Projection('customer', ['CUSTKEY', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'MKTSEGMENT']),
    GroupBy('customer', 'NATIONKEY'),
    Aggregate('customer', 'max'),
  ]

  q3 = [
    Selection(
      'lineitem',
      conditions=[
        Condition('SUPPKEY', Operator.gt, 100),
        ConditionalOperator.OR,
        Condition('QUANTITY', Operator.gt, 5),
      ],
    ),
  ]
  q4 = [
    Selection(
      'lineitem',
      conditions=[
        Condition('SUPPKEY', Operator.gt, 100),
        ConditionalOperator.OR,
        Condition('QUANTITY', Operator.gt, 5),
        ConditionalOperator.AND,
        Condition('DISCOUNT', Operator.gt, 0.05),
      ],
    ),
    Projection(
      'lineitem',
      [
        'PARTKEY',
        'SUPPKEY',
        'LINENUMBER',
        'QUANTITY',
        'DISCOUNT',
        'TAX',
        'SHIPDATE',
      ],
    ),
  ]

  q5 = [
    Selection(
      'lineitem',
      conditions=[
        Condition('SUPPKEY', Operator.gt, 100),
        ConditionalOperator.OR,
        Condition('QUANTITY', Operator.gt, 5),
        ConditionalOperator.AND,
        Condition('DISCOUNT', Operator.gt, 0.05),
      ],
    ),
    Projection(
      'lineitem',
      [
        'PARTKEY',
        'SUPPKEY',
        'LINENUMBER',
        'QUANTITY',
        'RETURNFLAG',
        'DISCOUNT',
        'TAX',
        'SHIPDATE',
        'SHIPMODE',
      ],
    ),
    GroupBy('lineitem', 'RETURNFLAG'),
    Aggregate('lineitem', 'min'),
  ]
  q6 = [
    Selection('nation', conditions=[Condition('REGIONKEY', Operator.gt, 0)]),
    Projection('nation', ['REGIONKEY', 'N_NAME', 'N_COMMENT']),
  ]

  q7 = [Selection('region', conditions=[Condition('REGIONKEY', Operator.ge, 0)])]

  q8 = [
    Selection(
      'orders',
      conditions=[
        Condition('TOTALPRICE', Operator.gt, 50000.0),
        ConditionalOperator.OR,
        Condition('SHIPPRIORITY', Operator.eq, 0),
      ],
    ),
    Projection('orders', ['CUSTKEY', 'TOTALPRICE', 'ORDERPRIORITY', 'CLERK']),
  ]

  q9 = [
    Selection(
      'orders',
      conditions=[
        Condition('TOTALPRICE', Operator.gt, 50000.0),
        ConditionalOperator.OR,
        Condition('SHIPPRIORITY', Operator.eq, 0),
      ],
    ),
    Projection(
      'orders',
      ['ORDERSTATUS', 'CUSTKEY', 'TOTALPRICE', 'ORDERPRIORITY', 'CLERK'],
    ),
    GroupBy('orders', 'ORDERSTATUS'),
    Aggregate('orders', 'max'),
  ]
  q10 = [
    Selection(
      'supplier',
      conditions=[
        Condition('NATIONKEY', Operator.gt, 10),
        ConditionalOperator.OR,
        Condition('ACCTBAL', Operator.le, 5000),
      ],
    ),
    Projection('supplier', ['S_NAME', 'NATIONKEY', 'ACCTBAL']),
  ]
  q11 = [
    Selection(
      'supplier',
      conditions=[
        Condition('NATIONKEY', Operator.gt, 10),
        ConditionalOperator.OR,
        Condition('ACCTBAL', Operator.le, 5000),
      ],
    ),
  ]
  q12 = [Selection('part', conditions=[Condition('RETAILPRICE', Operator.gt, 500)])]

  q13 = [Selection('partsupp', conditions=[Condition('SUPPLYCOST', Operator.le, 1000)])]

  pq1 = Query(q1, source=customer)
  pq2 = Query(q2, source=customer)
  pq3 = Query(q3, source=lineitem)
  pq4 = Query(q4, source=lineitem)
  pq5 = Query(q5, source=lineitem)
  pq6 = Query(q6, source=nation)
  pq7 = Query(q7, source=region)
  pq8 = Query(q8, source=orders)
  pq9 = Query(q9, source=orders)
  pq10 = Query(q10, source=supplier)
  pq11 = Query(q11, source=supplier)
  pq12 = Query(q12, source=part)
  pq13 = Query(q13, source=partsupp)

  allqueries = [
    pq1,
    pq2,
    pq3,
    pq4,
    pq5,
    pq6,
    pq7,
    pq8,
    pq9,
    pq10,
    pq11,
    pq12,
    pq13,
  ]
  # allqueries = [pq4]
  res = []
  count = 1
  # c = pq3.get_new_pandas_queries()
  for pq in allqueries:
    print(f'*** query #{count} is generating ***')
    count += 1
    res += pq.get_new_pandas_queries()[:100]

  print('done')

  pandas_queries_list = QueryPool(res)
  pandas_queries_list.generate_possible_merge_operations()


def add_foreignkeys(TBL1: TableSource, col1, TBL2: TableSource, col2):
  TBL1.add_edge(col1, col2, TBL2)
  TBL2.add_edge(col2, col1, TBL1)


# Command-line interface
if __name__ == '__main__':
  import argparse
  import json
  import string

  # To measure total execution time of the query generator
  start = time.time()

  parser = argparse.ArgumentParser(description='Pandas Query Generator CLI')

  parser.add_argument(
    '--schema',
    type=str,
    required=True,
    help='Path to the relational schema JSON file',
  )

  parser.add_argument(
    '--params',
    type=str,
    required=True,
    help='Path to the user-defined parameters JSON file',
  )

  parser.add_argument(
    '--export-directory',
    type=str,
    required=False,
    default='./results',
    help='Path to export results to',
  )

  parser.add_argument(
    '--verbose',
    type=bool,
    required=False,
    default=False,
    help='Whether or not to print extra generation information',
  )

  args = parser.parse_args()

  with open(args.schema, 'r') as sf:
    schema_info = json.load(sf)

  with open(args.params, 'r') as pf:
    params = json.load(pf)

  # Extract parameters
  num_merges = params.get('num_merges', 2)
  num_queries = params.get('num_queries', 1000)
  multi_line = params.get('multi_line', False) == 'True'

  # Initialize dictionaries to store DataFrames and their respective meta information
  dataframes = {}
  data_ranges = {}
  foreign_keys = {}
  table_sources = {}
  primary_keys = {}

  # Function to extract and store data ranges from JSON schema properties
  def extract_data_ranges(properties):
    ranges = {}
    for prop, info in properties.items():
      if 'min' in info and 'max' in info:  # Check if min and max values are defined
        ranges[prop] = (info['min'], info['max'])
      elif info['type'] == 'string':
        ranges[prop] = (info.get('starting character'),)
      elif info['type'] == 'enum':
        ranges[prop] = info['values']
    return ranges

  # Function to populate DataFrame with rows of random data based on schema
  def create_dataframe(entity_schema, num_rows=100, primary_key_unique=True):
    rows = []
    # If the primary key is unique, then num_rows for that dataframe = min(properties['max'] - properties['min'] + 1, 200)
    if primary_key_unique:
      num_rows = min(
        entity_schema['properties'][entity_schema['primary_key']]['max']
        - entity_schema['properties'][entity_schema['primary_key']]['min']
        + 1,
        200,
      )

    for i in range(num_rows):
      row = {}
      for column, properties in entity_schema['properties'].items():
        if properties['type'] == 'int':
          # Generate unique values for primary key
          if (
            primary_key_unique
            and column == entity_schema['primary_key']
            and num_rows == (properties['max'] - properties['min'] + 1)
          ):
            row[column] = i + properties['min']
          else:
            row[column] = random.randint(properties['min'], properties['max'])
        elif properties['type'] == 'float':  # For 'number', assuming float
          row[column] = round(random.uniform(properties['min'], properties['max']), 2)
        elif properties['type'] == 'string':
          # Ensure the string starts with one of the starting characters
          starting_char = random.choice(properties['starting character'])
          random_string = ''.join(
            random.choices(string.ascii_letters, k=9)
          )  # Generate 9 random characters
          row[column] = starting_char + random_string
        elif properties['type'] == 'enum':
          row[column] = random.choice(properties['values'])
        elif properties['type'] == 'date':
          min_date = pd.to_datetime(properties['min'])
          max_date = pd.to_datetime(properties['max'])
          row[column] = pd.to_datetime(random.choice(pd.date_range(min_date, max_date))).strftime(
            '%Y-%m-%d'
          )
      rows.append(row)
    return pd.DataFrame(rows)

  for entity, entity_info in schema_info['entities'].items():
    entity_schema = {
      'properties': entity_info['properties'],
      'primary_key': entity_info.get('primary_key', None),
      'foreign_keys': entity_info.get('foreign_keys', {}),
    }

    # dynamic create variable names to reference df with globals()[entity]
    if not isinstance(entity_schema['primary_key'], list):
      globals()[entity] = create_dataframe(entity_schema, num_rows=200, primary_key_unique=True)

    else:
      globals()[entity] = create_dataframe(entity_schema, num_rows=200, primary_key_unique=False)

    dataframes[entity] = globals()[entity]

    # tbl_source for each dataframe
    tbl = TableSource(globals()[entity], entity)
    table_sources[entity] = tbl

    # extract_data_ranges
    ranges = extract_data_ranges(entity_info['properties'])
    data_ranges[entity] = ranges

    # primary_key
    primary_key = entity_info['primary_key']
    primary_keys[entity] = primary_key

    if 'foreign_keys' in entity_info:
      foreign_keys[entity] = []
      for fk_column, refers_to in entity_info['foreign_keys'].items():
        foreign_keys[entity].append((fk_column, refers_to[0], refers_to[1]))

  # Add foreign keys info to tbl_sources
  for entity, listT in foreign_keys.items():
    for tuple in listT:
      col, other_col, other = tuple
      add_foreignkeys(table_sources[entity], col, table_sources[other], other_col)

  end2 = time.time()

  # Base queries
  allqueries = []
  for entity, source in table_sources.items():
    allqueries += source.gen_base_queries(params)

  res = []
  count = 1

  end3 = time.time()
  # for data_structure.json, generates 4 queries for each of the 5 entities, so 20 pandas query objects
  for pq in allqueries:
    print(f'*** query #{count} is generating ***')
    count += 1
    # each pandas query object generates up to 100 unmerged pandas queries (depending on how many valid queries from gen_queries)
    res += pq.get_new_pandas_queries(params)[:100]

  end4 = time.time()

  print('done')

  # create pandas_query_pool object with list of unmerged queries and generate merge operations on them
  pandas_queries_list = QueryPool(res, verbose=args.verbose)
  pandas_queries_list.shuffle_queries()

  # can't be merged if data schema is too simple (too few columns), generates 1000 merged queries with 3 merges each by default
  # Some of the merged queries are invalid (outputs “Exception occurred” and not saved in merged_queries.txt)
  pandas_queries_list.generate_possible_merge_operations(
    params, max_merge=num_merges, max_q=num_queries
  )

  end5 = time.time()

  if multi_line:
    pandas_queries_list.save_merged_examples_multiline(
      directory=args.export_directory, filename='merged_queries_auto_sf0000'
    )
  else:
    pandas_queries_list.save_merged_examples(args.export_directory, 'merged_queries_auto_sf0000')

  end = time.time()

  # print total time taken at each step of the query generation process
  print(f'Total time taken: {end - start} seconds')
  print(f'Time taken to create dataframes and parse relational schema: {end2 - start} seconds')
  print(f'Time taken to generate base queries: {end3 - end2} seconds')
  print(f'Time taken to generate unmerged queries: {end4 - end3} seconds')
  print(f'Time taken to generate merged queries: {end5 - end4} seconds')
  print(f'Time taken to save merged queries: {end - end5} seconds')
