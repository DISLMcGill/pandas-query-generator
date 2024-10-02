import builtins

import pytest
from pytest_mock import MockerFixture

from pandas_query_generator import ComparisonOperator, Condition, ConditionalOperator, Selection


@pytest.fixture
def sample_condition():
  return Condition('age', ComparisonOperator.GT, 30)


@pytest.fixture
def sample_selection(sample_condition):
  return Selection('df', [sample_condition])


def test_selection_initialization(sample_condition):
  selection = Selection('df', [sample_condition])
  assert selection.df_name == 'df'
  assert len(selection.conditions) == 1
  assert selection.conditions[0] == sample_condition
  assert selection.leading == True
  assert selection.count is None


def test_selection_str_representation(sample_selection):
  expected_str = "Selection: df_name = df, conditions = ['Condition(age, >, 30)']"
  assert str(sample_selection) == expected_str


def test_new_selection(sample_selection):
  new_condition = Condition('height', ComparisonOperator.LT, 180)
  new_selection = sample_selection.new_selection([new_condition])
  assert new_selection.df_name == 'df'
  assert len(new_selection.conditions) == 1
  assert new_selection.conditions[0] == new_condition


def test_to_str_single_condition(sample_selection):
  expected_str = "df[(df['age'] > 30)]"
  assert sample_selection.to_str() == expected_str


def test_to_str_multiple_conditions():
  conditions = [
    Condition('age', ComparisonOperator.GT, 30),
    ConditionalOperator.AND,
    Condition('height', ComparisonOperator.LT, 180),
  ]

  selection = Selection('df', conditions)

  expected_str = "df[(df['age'] > 30) & (df['height'] < 180)]"

  assert selection.to_str() == expected_str


def test_to_str_with_date_condition():
  condition = Condition('date', ComparisonOperator.EQ, '2023-01-01')
  selection = Selection('df', [condition])
  expected_str = "df[(df['date'] == '2023-01-01')]"
  assert selection.to_str() == expected_str


def test_to_str_with_in_condition():
  condition = Condition('category', ComparisonOperator.IN, ['A', 'B', 'C'])
  selection = Selection('df', [condition])
  expected_str = "df[(df['category'].isin(['A', 'B', 'C']))]"
  assert selection.to_str() == expected_str


def test_to_str_with_starts_with_condition():
  condition = Condition('name', ComparisonOperator.STARTS_WITH, 'A')
  selection = Selection('df', [condition])
  expected_str = "df[(df['name'].str.startswith('A'))]"
  assert selection.to_str() == expected_str


def test_is_logically_consistent_true():
  conditions = [
    Condition('age', ComparisonOperator.GT, 30),
    ConditionalOperator.AND,
    Condition('height', ComparisonOperator.LT, 180),
  ]

  selection = Selection('df', conditions)

  assert selection.is_logically_consistent() == True


def test_is_logically_consistent_false():
  conditions = [
    Condition('age', ComparisonOperator.GT, 30),
    ConditionalOperator.AND,
    Condition('age', ComparisonOperator.LT, 20),
  ]

  selection = Selection('df', conditions)

  assert selection.is_logically_consistent() == False


def test_is_logically_consistent_with_or():
  conditions = [
    Condition('age', ComparisonOperator.GT, 30),
    ConditionalOperator.OR,
    Condition('age', ComparisonOperator.LT, 20),
  ]

  selection = Selection('df', conditions)

  assert selection.is_logically_consistent() == True


def test_exec(mocker: MockerFixture):
  selection = Selection('df', [Condition('age', ComparisonOperator.GT, 30)])

  eval_spy = mocker.spy(builtins, 'eval')

  try:
    selection.exec()
  except Exception as e:
    print(f'Ignoring exception: {e}...')

  eval_spy.assert_called_once_with("df[(df['age'] > 30)]")


if __name__ == '__main__':
  pytest.main()
