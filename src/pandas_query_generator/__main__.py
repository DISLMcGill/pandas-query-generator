import itertools
import random
import sys
import time
import typing as t
import warnings
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .aggregate import Aggregate
from .arguments import Arguments
from .condition import Condition
from .group_by import GroupBy
from .merge import Merge
from .operation import Operation
from .operators import ComparisonOperator, ConditionalOperator
from .projection import Projection
from .query_structure import QueryStructure
from .schema import Schema
from .selection import Selection

warnings.filterwarnings('ignore', 'Boolean Series key will be reindexed to match DataFrame index.')


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

  def __init__(self, q_gen_query: t.List[Operation], table_source: 'TableSource', verbose=False):
    """
    Initialize a pandas_query object.

    :param q_gen_query: List of query operations (of type `operation`).
    :param source: The DataFrame or TBL_source object that is the target of the query.
    :param verbose: Whether to print the query string.
    """

    if verbose:
      print(self.get_query_string())

    self._source_ = table_source  ### TODO: modify to list of dataframes
    self._source_pandas_q = ''
    self.df_name = q_gen_query[0].df_name
    self.merged = False
    self.num_merges = 0
    self.pre_gen_query = self.setup_query(q_gen_query)
    self.query_string = self.get_query_string()
    self.target = self.execute_query()

    self.operations = [
      'select',
      'merge',
      'order',
      'concat',
      'rename',
      'groupby',
    ]

    # Initialize list of source tables for merged queries
    self.source_tables = [self.get_table_source()]

    # Initialize list of source dataframes for merged queries
    self.source_dataframes = [self.get_source()]

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
    return len(self.target.columns) > 0

  def do_a_projection(self) -> Projection | t.List[pd.Index]:
    """
    Create a projection operation with a random selection of columns.

    :return: A projection operation object.
    """
    columns = self.get_target().columns

    if len(columns) == 1:
      return [columns]
    else:
      # Select a random number of columns to project on
      res = [
        list(i) for i in list(itertools.combinations(columns, random.randrange(1, len(columns), 1)))
      ]

      random.shuffle(res)

      return Projection(self.df_name, res[0])

  def target_possible_selections(self, length=50) -> t.Dict[str, t.List[Condition]]:  # not used
    """
    Generate a dictionary of possible selection conditions based on numerical columns.

    :param length: The maximum number of conditions to generate for each column.
    :return: A dictionary mapping column names to lists of conditions.
    """
    # dictionary with col name as key and its data type as value
    possible_selection_columns = {}

    source_df = self.get_target()

    for _, col in enumerate(source_df.columns):
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
      for _ in range(length):
        if possible_selection_columns[key] == 'int':
          # add up to one std to randomly chosen statistic
          cur_val = round(description[random.choice(stats)]) + random.randrange(
            0, description['std'] + 1, 1
          )
        else:
          cur_val = float(
            description[random.choice(stats)] + random.randrange(0, description['std'] + 1, 1)
          )

        OPs = [
          ComparisonOperator.GT,
          ComparisonOperator.GE,
          ComparisonOperator.LE,
          ComparisonOperator.EQ,
          ComparisonOperator.LT,
          ComparisonOperator.NE,
        ]

        cur_condition = Condition(key, random.choice(OPs), cur_val)
        possible_condition_columns[key].append(cur_condition)
    return possible_condition_columns

  # difference with previous method?
  def possible_selections(self, length=50) -> t.Dict[str, t.List[Condition]]:
    """
    Generate a dictionary of possible selection conditions for each numerical column.

    :param length: The maximum number of conditions to generate for each column.
    :return: A dictionary mapping column names to lists of conditions.
    """
    possible_selection_columns = {}

    source_df = self.get_source()

    for _, col in enumerate(source_df.columns):
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
      for _ in range(length):
        if possible_selection_columns[key] == 'int':
          min_val, max_val = data_ranges[self.df_name][
            key
          ]  # data_ranges dict initialized in __main__, stores data ranges of each column for df_name
          cur_val = random.randint(min_val, max_val)
          # Ensure no conditions are created with values out of range
          if min_val == max_val:
            op = ComparisonOperator.EQ
          elif cur_val == min_val:
            op = random.choice(
              [
                ComparisonOperator.GT,
                ComparisonOperator.GE,
                ComparisonOperator.EQ,
                ComparisonOperator.NE,
              ]
            )
          elif cur_val == max_val:
            op = random.choice(
              [
                ComparisonOperator.LT,
                ComparisonOperator.LE,
                ComparisonOperator.EQ,
                ComparisonOperator.NE,
              ]
            )
          else:
            op = random.choice(
              [
                ComparisonOperator.GT,
                ComparisonOperator.GE,
                ComparisonOperator.LT,
                ComparisonOperator.LE,
                ComparisonOperator.EQ,
                ComparisonOperator.NE,
              ]
            )
          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'float':
          min_val, max_val = data_ranges[self.df_name][key]
          cur_val = round(random.uniform(min_val, max_val), 2)  # Assume 2 decimal places
          # Ensure no conditions are created with values out of range, no == or != operators for floats
          if min_val == max_val:
            op = ComparisonOperator.EQ
          elif cur_val == min_val:
            op = random.choice([ComparisonOperator.GT, ComparisonOperator.GE])
          elif cur_val == max_val:
            op = random.choice([ComparisonOperator.LT, ComparisonOperator.LE])
          else:
            op = random.choice(
              [
                ComparisonOperator.GT,
                ComparisonOperator.GE,
                ComparisonOperator.LT,
                ComparisonOperator.LE,
              ]
            )

          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'string':
          cur_val = random.choice(data_ranges[self.df_name][key][0])  # starting char
          cur_condition = Condition(key, ComparisonOperator.STARTS_WITH, cur_val)

        elif possible_selection_columns[key] == 'date':
          min_val, max_val = data_ranges[self.df_name][key]
          min_date = pd.to_datetime(min_val, format='%Y-%m-%d')
          max_date = pd.to_datetime(max_val, format='%Y-%m-%d')
          cur_val = pd.to_datetime(random.choice(pd.date_range(min_date, max_date))).strftime(
            '%Y-%m-%d'
          )
          if min_val == max_val:
            op = ComparisonOperator.EQ
          elif cur_val == min_val:
            op = random.choice([ComparisonOperator.GT, ComparisonOperator.GE])
          elif cur_val == max_val:
            op = random.choice([ComparisonOperator.LT, ComparisonOperator.LE])
          else:
            op = random.choice(
              [
                ComparisonOperator.GT,
                ComparisonOperator.GE,
                ComparisonOperator.LT,
                ComparisonOperator.LE,
              ]
            )
          cur_condition = Condition(key, op, cur_val)

        elif possible_selection_columns[key] == 'enum':
          if random.choice([True, False]):  # Randomly choose between == and IN condition
            cur_val = f"'{random.choice(data_ranges[self.df_name][key])}'"
            op = random.choice([ComparisonOperator.EQ, ComparisonOperator.NE])
            cur_condition = Condition(key, op, cur_val)
          else:
            num_in_values = random.randint(2, len(data_ranges[self.df_name][key]))
            in_values = [
              val for val in random.sample(data_ranges[self.df_name][key], num_in_values)
            ]
            cur_condition = Condition(key, ComparisonOperator.IN, in_values)

        possible_condition_columns[key].append(cur_condition)

    return possible_condition_columns

  def get_table_source(self) -> 'TableSource':
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

  def setup_query(self, list_op: t.List[Operation]) -> t.List[Operation]:
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

  def gen_queries(
    self, query_structure: QueryStructure, max_range=1000
  ) -> t.List[t.List[Operation]]:
    """
    :param query_structure: How the generated query should be structured
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

        num_selections = query_structure.num_selections

        for _ in range(max_range):
          while True:
            selection_length = random.randint(0, num_selections)
            cur_conditions = []
            cur_conditionsString = []
            and_count = 0  # count the number of & operators
            for _ in range(selection_length):
              cur_key = random.choice(list(possible_conditions_dict.keys()))  # key is col name
              cur_condition = random.choice(
                possible_conditions_dict[cur_key]
              )  # cur_condition is list of conditions

              if cur_condition.op != ComparisonOperator.STARTS_WITH:  # int or float col
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
        new_operations = self.generate_possible_column_combinations()

        for ops in new_operations:
          possible_new_operations.append(operation.new_projection(ops))

      generated_queries.append(possible_new_operations)

      print('===== possible operations generated =====')

    new_generated_queries = []
    new_generated_queries = itertools.product(*generated_queries)  # op1.1*op2.3*op3.2

    return [item for item in new_generated_queries]

  def get_new_pandas_queries(self, query_structure: QueryStructure, out=100) -> t.List['Query']:
    """
    Generate new pandas queries based on the existing operations.

    :param params: Dictionary storing user-defined query parameters.
    :param out: Maximum number of queries to generate.
    :return: List of pandas_query objects.
    """
    res = []  # stores pandas query objects generated

    new_queries = self.gen_queries(
      query_structure
    )  # list of tuples, each tuple contains a combination of query operations

    random.shuffle(new_queries)  # Shuffle to avoid bias towards conditions of the first column
    new_queries = new_queries[:out]

    print(f' ==== Testing source with {len(new_queries)} queries ==== ')

    tbl = (
      self.get_table_source()
    )  # Assuming this gets some source necessary for query object creation

    progress_interval = max(1, len(new_queries) // 10)  # Ensure no division by zero

    for i, new_query in enumerate(new_queries):
      if i % progress_interval == 0:
        print(
          f'=== {i // progress_interval * 10}% ==='
        )  # for every 10%, indicates current % of new queries generated

      # Assume execute_query() is a method that takes a query and executes it against the DataFrame
      try:
        new_q_obj = Query(
          new_query, tbl
        )  # create pandas_query object for each query executed on source tbl

        res.append(new_q_obj)
      except:
        continue

    random.shuffle(res)  # shuffle result to ensure diverse order of queries

    print(f' ======= {len(res)} new queries generated =======')

    return res  # returns list of pandas query objects

  def validate_results(self, res: t.List['Query']) -> bool:
    """
    Check if the queries are in good grammar.

    :param res: List of pandas_query objects.
    :return: True
    """
    true_count = false_count = 0

    for r in res:
      try:
        eval(r.query_string)
      except Exception:
        false_count += 1
        continue
      true_count += 1

    print(f'%%%%%%%%%% truecount = {true_count}; false count = {false_count} %%%%%%%%%%%%')

    return True

  def execute_query(self) -> pd.DataFrame:
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
      'tbl_sources': table_sources,
    }

    return pd.eval(query_string, local_dict=local_dict)

  def generate_possible_groupby_combinations(self, limit=5) -> t.List[str]:
    """
    Generate possible combinations of columns for groupby operations.

    :param generate_num: Maximum number of combinations to generate.
    :return: List of column names to group by.
    """
    columns = self.get_source().columns

    possible_groupby_columns = []

    for col in columns:
      possible_groupby_columns.append(col)

    random.shuffle(possible_groupby_columns)

    return possible_groupby_columns[:limit]

  def generate_possible_column_combinations(
    self, limit=50
  ) -> t.List[t.List[str]] | t.List[pd.Index]:
    """
    Generate possible combinations of columns for projection operations.

    :param operation: A projection operation.
    :param generate_num: Maximum number of combinations to generate.
    :return: List of lists of column combinations.
    """
    columns = self.get_source().columns

    if len(columns) == 1:
      return [columns]
    else:
      res = []

      for length in range(1, len(columns) + 1):
        res += [list(i) for i in list(itertools.combinations(columns, length))]

      random.shuffle(res)

      return res[:limit]

  def generate_possible_selection_operations(
    self, possible_new_conditions, generate_num=100
  ) -> t.List[t.List[t.Union[Condition, ConditionalOperator]]]:
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

    for _ in range(generate_num):
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
          possible_new_ith_condition.op in [ComparisonOperator.EQ, ComparisonOperator.NE]
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


class QueryPool:
  result_queries: t.List[t.Any]

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

  def __init__(self, queries: t.List[Query], count=0, self_join=False, verbose=True):
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
    self.verbose = verbose

    # Stores a copy of the original queries to generate unmerged examples
    self.un_merged_queries = queries[:]

  def save(self, directory: str, filename: str, multi_line: t.Optional[bool] = False) -> None:
    """
    Save the merged queries into a text file.

    This method writes the generated queries to a file, either in a single-line
    or multi-line format. It creates the directory if it doesn't exist and
    handles potential exceptions during the file writing process.

    Args:
      directory (str): The directory path where the file should be saved.
      filename (str): The name of the file to save (without extension).
      multi_line (bool, optional): Whether to save queries in a multi-line format. Defaults to False.

    Raises:
      IOError: If there's an error writing to the file.

    Note:
      The multi-line format is more verbose and includes intermediate steps.
      The single-line format is more compact and only includes the final queries.
    """
    filepath = Path(directory) / f'{filename}.txt'

    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
      if multi_line:
        self._save_multi_line(filepath)
      else:
        self._save_single_line(filepath)
      print(f'Successfully wrote the merged queries into file {filepath}')
    except IOError as e:
      print(f'Error writing to file {filepath}: {e}')

  def _save_single_line(self, filepath: Path) -> None:
    """Save queries in a single-line format."""
    content = '\n'.join(f'df{i} = {q.query_string}' for i, q in enumerate(self.result_queries))
    filepath.write_text(content)

  def _save_multi_line(self, filepath: Path) -> None:
    """Save queries in a multi-line format."""

    class QueryUnraveler:
      def __init__(self):
        self.exception_count = 0
        self.count = 0

      def unravel(self, query: Query, file):
        try:
          eval(query.pre_gen_query)
        except Exception:
          self.exception_count += 1

        for operation in query.pre_gen_query:
          if isinstance(operation, Merge):
            counter = self.count - 1

            self.unravel(operation.queries, file)

            file.write(
              f'df{self.count} = df{counter}.merge(df{self.count - 1}, '
              f'left_on={operation.left_on}, right_on={operation.right_on})\n'
            )
          else:
            op_str = operation.to_str()

            if operation.leading:
              file.write(f'df{self.count} = {op_str}\n')
            else:
              if isinstance(operation, Selection):
                op_str = operation.to_str(str(self.count - 1))
              file.write(f'df{self.count} = df{self.count - 1}{op_str}\n')

          self.count += 1

    unraveler = QueryUnraveler()

    with filepath.open('w') as file:
      for query in self.result_queries:
        unraveler.unravel(query, file)
        file.write('Next\n')

    if unraveler.exception_count > 0:
      print(f'Warning: {unraveler.exception_count} exceptions occurred during query evaluation')

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

    if isinstance(q1.get_target(), pd.Series) or isinstance(q2.get_target(), pd.Series):
      return []

    col1 = list(q1.get_target().columns)
    col2 = list(q2.get_target().columns)

    q1_foreign_keys = q1.get_table_source().get_foreign_keys()
    q2_foreign_keys = q2.get_table_source().get_foreign_keys()

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

  def generate_possible_merge_operations(
    self, query_structure: QueryStructure, max_merge=3, max_q=5000
  ):
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

      if random.random() > 0.5 and query_structure.group_by and query_structure.aggregation:
        operations = list(query.pre_gen_query)[:]
        operations_with_groupby_agg = operations[:]

        groupby_column = query.generate_possible_groupby_combinations(limit=1)

        operations_with_groupby_agg.append(GroupBy(query.df_name, groupby_column))
        operations_with_groupby_agg.append(Aggregate(query.df_name, random.choice(stats)))

        new_query_with_groupby_agg = Query(
          operations_with_groupby_agg, query.get_table_source(), verbose=False
        )
        self.result_queries.append(new_query_with_groupby_agg)

      elif random.random() > 0.5 and not query_structure.group_by and query_structure.aggregation:
        operations = list(query.pre_gen_query)[:]
        operations_with_agg = operations[:]

        operations_with_agg.append(Aggregate(query.df_name, random.choice(stats)))

        new_query_with_agg = Query(operations_with_agg, query.get_table_source(), verbose=False)
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
                if rand > 0.5 and len(columns) and query_structure.projection:
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
              new_query = Query(operations, q1.get_table_source(), verbose=False)

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
                  random.random() > 0.5 and query_structure.group_by and query_structure.aggregation
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
                    q1.get_table_source(),
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
                  and not query_structure.group_by
                  and query_structure.aggregation
                ):
                  operations_with_groupby_agg.append(Aggregate(df_name, random.choice(stats)))

                  new_query_with_agg = Query(
                    operations_with_groupby_agg,
                    q1.get_table_source(),
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

                new_query = Query(operations, q1.get_table_source(), verbose=False)
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

  def __init__(self, df: pd.DataFrame, name: str) -> None:
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

  def generate_selection(self) -> Selection:
    """
    perform a random selection on the dataframe
    :return: an object of type selection
    """
    possible_selection_columns = self.source.columns.tolist()

    if not possible_selection_columns:
      raise ValueError('No suitable numerical columns available for selection.')

    choice_col = random.choice(possible_selection_columns)

    min_val = max_val = num = 0

    if self.source[choice_col].dtype.kind in 'if':  # Check if the column is float or int
      min_val, max_val = data_ranges[self.name][choice_col]

      num = random.uniform(min_val, max_val)

      if self.source[choice_col].dtype.kind == 'i':  # If it's an int, round it
        num = round(num)

    if self.source[choice_col].dtype.kind == 'i':
      if min_val == max_val:
        op_choice = ComparisonOperator.EQ
      elif num == min_val:
        op_choice = random.choice(
          [
            ComparisonOperator.GT,
            ComparisonOperator.GE,
            ComparisonOperator.EQ,
            ComparisonOperator.NE,
          ]
        )
      elif num == max_val:
        op_choice = random.choice(
          [
            ComparisonOperator.LT,
            ComparisonOperator.LE,
            ComparisonOperator.EQ,
            ComparisonOperator.NE,
          ]
        )
      else:
        op_choice = random.choice(
          [
            ComparisonOperator.GT,
            ComparisonOperator.GE,
            ComparisonOperator.LT,
            ComparisonOperator.LE,
            ComparisonOperator.EQ,
            ComparisonOperator.NE,
          ]
        )

    elif self.source[choice_col].dtype.kind == 'f':
      if min_val == max_val:
        op_choice = ComparisonOperator.EQ
      elif num == min_val:
        op_choice = random.choice([ComparisonOperator.GT, ComparisonOperator.GE])
      elif num == max_val:
        op_choice = random.choice([ComparisonOperator.LT, ComparisonOperator.LE])
      else:
        op_choice = random.choice(
          [
            ComparisonOperator.GT,
            ComparisonOperator.GE,
            ComparisonOperator.LT,
            ComparisonOperator.LE,
          ]
        )

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
          op_choice = ComparisonOperator.EQ
        elif num == min_date:
          op_choice = random.choice([ComparisonOperator.GT, ComparisonOperator.GE])
        elif num == max_date:
          op_choice = random.choice([ComparisonOperator.LT, ComparisonOperator.LE])
        else:
          op_choice = random.choice(
            [
              ComparisonOperator.GT,
              ComparisonOperator.GE,
              ComparisonOperator.LT,
              ComparisonOperator.LE,
            ]
          )
      except ValueError:
        startL = data_ranges[self.name][choice_col][0]
        num = random.choice(startL)  # starting char
        op_choice = ComparisonOperator.STARTS_WITH

    # enum values are stored in lists in data ranges
    elif (
      self.source[choice_col].dtype == 'object' or self.source[choice_col].dtype == 'string'
    ) and isinstance(data_ranges[self.name][choice_col], list):
      if random.choice([True, False]):
        num = f"'{random.choice(data_ranges[self.name][choice_col])}'"
        op_choice = random.choice([ComparisonOperator.EQ, ComparisonOperator.NE])
      else:
        num_in_values = random.randint(2, len(data_ranges[self.name][choice_col]))
        in_values = [
          val for val in random.sample(data_ranges[self.name][choice_col], num_in_values)
        ]
        op_choice = ComparisonOperator.IN
        num = in_values

    cur_condition = Condition(
      choice_col, op_choice, num
    )  # don't need to check consistency since only one condition

    return Selection(self.name, [cur_condition])

  def generate_projection(self) -> Projection:
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

  def generate_base_queries(self, query_structure: QueryStructure) -> t.List[Query]:
    """
    Customized generation with base queries, can be modified to fit in various circumstances
    param query_types: types of queries specified by the user
    :return: List[pandas_query]
    """

    q_gen_query_1 = []
    q_gen_query_2 = []
    q_gen_query_3 = []
    q_gen_query_4 = []

    if query_structure.num_selections > 0 and query_structure.projection:
      q_gen_query_1.append(self.generate_projection())
      q_gen_query_2.append(self.generate_selection())
      q_gen_query_3.append(self.generate_selection())
      q_gen_query_3.append(self.generate_projection())
      q_gen_query_4.append(self.generate_selection())
    elif query_structure.num_selections == 0 and query_structure.projection:
      q_gen_query_1.append(self.generate_projection())
      q_gen_query_2.append(self.generate_projection())
      q_gen_query_3.append(self.generate_projection())
      q_gen_query_4.append(self.generate_projection())
    elif query_structure.num_selections > 0 and not query_structure.projection:
      q_gen_query_1.append(self.generate_selection())
      q_gen_query_2.append(self.generate_selection())
      q_gen_query_3.append(self.generate_selection())
      q_gen_query_4.append(self.generate_selection())
    else:
      sys.exit(
        'Invalid parameters for generating base queries. Must have at least one selection or projection operation.'
      )

    return [
      Query(q_gen_query=q_gen_query_1, table_source=self),
      Query(q_gen_query=q_gen_query_2, table_source=self),
      Query(q_gen_query=q_gen_query_3, table_source=self),
      Query(q_gen_query=q_gen_query_4, table_source=self),
    ]


def test_run_TPCH(tpch_dataframes):
  table_sources = {name: TableSource(df, name) for name, df in tpch_dataframes.items()}

  query_definitions = [
    (
      'customer',
      [
        Selection(
          'customer',
          conditions=[
            Condition('ACCTBAL', ComparisonOperator.GT, 100),
            ConditionalOperator.OR,
            Condition('CUSTKEY', ComparisonOperator.LE, 70),
          ],
        ),
        Projection('customer', ['CUSTKEY', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'MKTSEGMENT']),
      ],
    ),
    (
      'customer',
      [
        Selection(
          'customer',
          conditions=[
            Condition('ACCTBAL', ComparisonOperator.GT, 100),
            ConditionalOperator.OR,
            Condition('CUSTKEY', ComparisonOperator.LE, 70),
          ],
        ),
        Projection('customer', ['CUSTKEY', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'MKTSEGMENT']),
        GroupBy('customer', 'NATIONKEY'),
        Aggregate('customer', 'max'),
      ],
    ),
    (
      'lineitem',
      [
        Selection(
          'lineitem',
          conditions=[
            Condition('SUPPKEY', ComparisonOperator.GT, 100),
            ConditionalOperator.OR,
            Condition('QUANTITY', ComparisonOperator.GT, 5),
          ],
        ),
      ],
    ),
    (
      'lineitem',
      [
        Selection(
          'lineitem',
          conditions=[
            Condition('SUPPKEY', ComparisonOperator.GT, 100),
            ConditionalOperator.OR,
            Condition('QUANTITY', ComparisonOperator.GT, 5),
            ConditionalOperator.AND,
            Condition('DISCOUNT', ComparisonOperator.GT, 0.05),
          ],
        ),
        Projection(
          'lineitem',
          ['PARTKEY', 'SUPPKEY', 'LINENUMBER', 'QUANTITY', 'DISCOUNT', 'TAX', 'SHIPDATE'],
        ),
      ],
    ),
    (
      'lineitem',
      [
        Selection(
          'lineitem',
          conditions=[
            Condition('SUPPKEY', ComparisonOperator.GT, 100),
            ConditionalOperator.OR,
            Condition('QUANTITY', ComparisonOperator.GT, 5),
            ConditionalOperator.AND,
            Condition('DISCOUNT', ComparisonOperator.GT, 0.05),
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
      ],
    ),
    (
      'nation',
      [
        Selection('nation', conditions=[Condition('REGIONKEY', ComparisonOperator.GT, 0)]),
        Projection('nation', ['REGIONKEY', 'N_NAME', 'N_COMMENT']),
      ],
    ),
    (
      'region',
      [
        Selection('region', conditions=[Condition('REGIONKEY', ComparisonOperator.GE, 0)]),
      ],
    ),
    (
      'orders',
      [
        Selection(
          'orders',
          conditions=[
            Condition('TOTALPRICE', ComparisonOperator.GT, 50000.0),
            ConditionalOperator.OR,
            Condition('SHIPPRIORITY', ComparisonOperator.EQ, 0),
          ],
        ),
        Projection('orders', ['CUSTKEY', 'TOTALPRICE', 'ORDERPRIORITY', 'CLERK']),
      ],
    ),
    (
      'orders',
      [
        Selection(
          'orders',
          conditions=[
            Condition('TOTALPRICE', ComparisonOperator.GT, 50000.0),
            ConditionalOperator.OR,
            Condition('SHIPPRIORITY', ComparisonOperator.EQ, 0),
          ],
        ),
        Projection(
          'orders',
          ['ORDERSTATUS', 'CUSTKEY', 'TOTALPRICE', 'ORDERPRIORITY', 'CLERK'],
        ),
        GroupBy('orders', 'ORDERSTATUS'),
        Aggregate('orders', 'max'),
      ],
    ),
    (
      'supplier',
      [
        Selection(
          'supplier',
          conditions=[
            Condition('NATIONKEY', ComparisonOperator.GT, 10),
            ConditionalOperator.OR,
            Condition('ACCTBAL', ComparisonOperator.LE, 5000),
          ],
        ),
        Projection('supplier', ['S_NAME', 'NATIONKEY', 'ACCTBAL']),
      ],
    ),
    (
      'supplier',
      [
        Selection(
          'supplier',
          conditions=[
            Condition('NATIONKEY', ComparisonOperator.GT, 10),
            ConditionalOperator.OR,
            Condition('ACCTBAL', ComparisonOperator.LE, 5000),
          ],
        ),
      ],
    ),
    (
      'part',
      [
        Selection('part', conditions=[Condition('RETAILPRICE', ComparisonOperator.GT, 500)]),
      ],
    ),
    (
      'partsupp',
      [
        Selection('partsupp', conditions=[Condition('SUPPLYCOST', ComparisonOperator.LE, 1000)]),
      ],
    ),
  ]

  structure = QueryStructure(
    aggregation=True,
    group_by=True,
    multi_line=False,
    num_merges=3,
    num_queries=1000,
    num_selections=2,
    projection=True,
  )

  queries = [Query(q, table_sources[table]) for table, q in query_definitions]

  res = []

  for query in queries:
    res.extend(query.get_new_pandas_queries(structure)[:100])

  pandas_queries_list = QueryPool(res)
  pandas_queries_list.generate_possible_merge_operations(structure)

  assert len(res) > 0, 'No queries were generated'
  assert len(pandas_queries_list.result_queries) > 0, 'No merged queries were generated'


# TODO(liam): Centralize data access in a single top-level structure.
dataframes = {}
data_ranges = {}
foreign_keys = {}
table_sources = {}
primary_keys = {}


def main():
  start_time = time.time()

  @contextmanager
  def timer(description):
    start = time.time()
    yield
    elapsed_time = time.time() - start
    print(f'Time taken for {description}: {elapsed_time:.2f} seconds')

  with timer('the entire query generation flow'):
    arguments = Arguments.from_args()

    with timer('creating dataframes and parsing relational schema'):
      schema, query_structure = (
        Schema.from_file(arguments.schema),
        QueryStructure.from_file(arguments.params),
      )

      for name, entity in schema.entities.items():
        # TODO(liam): Can we get rid of this globals hack?
        globals()[name] = dataframes[name] = entity.generate_dataframe(num_rows=200)

        table_sources[name] = TableSource(dataframes[name], name)
        data_ranges[name] = entity.data_ranges
        primary_keys[name] = entity.primary_key
        foreign_keys[name] = []

        for column, refers_to in entity.foreign_keys.items():
          foreign_keys[name].append((column, refers_to[0], refers_to[1]))

      for entity, elements in foreign_keys.items():
        for element in elements:
          col, other_col, other = element
          table_sources[entity].add_edge(col, other_col, table_sources[other])
          table_sources[other].add_edge(other_col, col, table_sources[entity])

    with timer('generating base queries'):
      queries = []

      for entity, source in table_sources.items():
        queries += source.generate_base_queries(query_structure)

    with timer('generating unmerged queries'):
      res, count = [], 1

      for query in queries:
        count += 1
        res += query.get_new_pandas_queries(query_structure)[:100]

    with timer('generating merged queries'):
      query_pool = QueryPool(res, verbose=arguments.verbose)

      query_pool.shuffle_queries()

      query_pool.generate_possible_merge_operations(
        query_structure,
        max_merge=query_structure.num_merges,
        max_q=query_structure.num_queries,
      )

    with timer('saving merged queries'):
      query_pool.save(
        directory=arguments.output_directory,
        filename='merged_queries_auto_sf0000',
        multi_line=query_structure.multi_line,
      )

  total_time = time.time() - start_time

  print(f'Total time taken: {total_time:.2f} seconds')


if __name__ == '__main__':
  main()
