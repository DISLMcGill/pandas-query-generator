import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from pandas_query_generator.group_by_aggregation import GroupByAggregation
from pandas_query_generator.merge import Merge
from pandas_query_generator.projection import Projection
from pandas_query_generator.query import Query
from pandas_query_generator.selection import Selection
from pandas_query_generator.utils import execute_query, generate_query_statistics


@pytest.fixture
def sample_dataframes():
  return {
    'customers': pd.DataFrame(
      {
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'country': ['US', 'UK', 'US'],
      }
    ),
    'orders': pd.DataFrame(
      {'id': [1, 2, 3, 4], 'customer_id': [1, 1, 2, 3], 'amount': [100, 200, 150, 300]}
    ),
  }


@pytest.fixture
def simple_selection():
  """Create a simple selection query."""
  return Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})


@pytest.fixture
def simple_projection():
  """Create a simple projection query."""
  return Query('customers', [Projection(['name', 'age'])], False, {'name', 'age'})


@pytest.fixture
def simple_groupby():
  """Create a simple groupby query."""
  return Query('customers', [GroupByAggregation(['country'], 'count')], False, {'country'})


@pytest.fixture
def simple_merge():
  """Create a simple merge query."""
  nested_query = Query('orders', [], False, set())
  return Query(
    'customers', [Merge(nested_query, "'id'", "'customer_id'")], False, {'id', 'customer_id'}
  )


class TestExecuteQuery:
  def test_simple_selection(self, sample_dataframes, simple_selection):
    result, error = execute_query(simple_selection, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 30]
    assert_frame_equal(result, expected)

  def test_simple_projection(self, sample_dataframes, simple_projection):
    result, error = execute_query(simple_projection, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'][['name', 'age']]
    assert_frame_equal(result, expected)

  def test_simple_groupby(self, sample_dataframes, simple_groupby):
    result, error = execute_query(simple_groupby, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'].groupby('country').agg('count')
    assert_frame_equal(result, expected)

  def test_simple_merge(self, sample_dataframes, simple_merge):
    result, error = execute_query(simple_merge, sample_dataframes)

    assert error is None

    expected = sample_dataframes['customers'].merge(
      sample_dataframes['orders'], left_on='id', right_on='customer_id'
    )

    assert_frame_equal(result, expected)

  def test_invalid_query(self, sample_dataframes):
    bad_query = Query(
      'customers',
      [Selection([("'nonexistent_column'", '>=', 30, '&')])],
      False,
      {'nonexistent_column'},
    )

    result, error = execute_query(bad_query, sample_dataframes)

    assert result is None
    assert error is not None
    assert 'KeyError' in error

  def test_empty_result(self, sample_dataframes):
    query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})
    result, error = execute_query(query, sample_dataframes)
    assert result is not None
    assert error is None
    assert result.empty


class TestGenerateQueryStatistics:
  def test_empty_queries(self):
    stats = generate_query_statistics([])
    assert stats['total_queries'] == 0
    assert stats['avg_operations_per_query'] == 0.0
    assert len(stats['operations']) == 0

  def test_query_type_counting(
    self, simple_selection, simple_projection, simple_groupby, simple_merge
  ):
    queries = [simple_selection, simple_projection, simple_groupby, simple_merge]
    stats = generate_query_statistics(queries)

    assert stats['total_queries'] == 4
    assert stats['operations']['Selection'] == 1
    assert stats['operations']['Projection'] == 1
    assert stats['operations']['GroupByAggregation'] == 1
    assert stats['operations']['Merge'] == 1

  def test_execution_results(self, sample_dataframes, simple_selection):
    result, error = execute_query(simple_selection, sample_dataframes)
    stats = generate_query_statistics([simple_selection], [(result, error)])

    assert stats['execution_results']['successful_executions'] == 1
    assert stats['execution_results']['failed_executions'] == 0
    assert stats['execution_results']['success_rate'] == 100.0

  def test_error_tracking(self, sample_dataframes):
    bad_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, '&')])], False, {'nonexistent'}
    )

    result, error = execute_query(bad_query, sample_dataframes)
    stats = generate_query_statistics([bad_query], [(result, error)])

    assert stats['execution_results']['failed_executions'] == 1
    assert stats['execution_results']['successful_executions'] == 0
    assert stats['execution_results']['success_rate'] == 0.0
    assert len(stats['execution_results']['errors']) > 0

  def test_statistics_aggregation(self, simple_selection, simple_merge):
    nested_query = Query(
      'orders',
      [Selection([("'amount'", '>', 100, '&')]), Projection(['amount', 'customer_id'])],
      False,
      {'amount', 'customer_id'},
    )

    complex_merge = Query(
      'customers', [Merge(nested_query, "'id'", "'customer_id'")], False, {'id', 'customer_id'}
    )

    queries = [simple_selection, simple_merge, complex_merge]
    stats = generate_query_statistics(queries)

    assert stats['total_queries'] == 3
    assert stats['merges'][0] == 1
    assert stats['merges'][2] == 1
    assert stats['selections'][1] == 1
    assert stats['avg_operations_per_query'] > 0


@pytest.fixture
def simple_selection_multi():
  """Create a simple selection query in multi-line format."""
  return Query(
    'customers',
    [Selection([("'age'", '>=', 30, '&')])],
    True,
    {'age'},
  )


@pytest.fixture
def complex_multi_line():
  """Create a complex multi-line query with multiple operations."""
  nested_query = Query(
    'orders',
    [Selection([("'amount'", '>', 100, '&')]), Projection(['amount', 'customer_id'])],
    True,
    {'amount', 'customer_id'},
  )

  return Query(
    'customers',
    [
      Selection([("'age'", '>=', 25, '&')]),
      Projection(['name', 'age', 'id']),
      Merge(nested_query, "'id'", "'customer_id'"),
      GroupByAggregation(['age'], 'mean'),
    ],
    True,
    {'id', 'name', 'age'},
  )


class TestMultiLineExecution:
  def test_simple_multi_line(self, sample_dataframes, simple_selection_multi):
    result, error = execute_query(simple_selection_multi, sample_dataframes)

    assert error is None

    expected = sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 30]

    assert_frame_equal(result, expected)

  def test_complex_multi_line(self, sample_dataframes, complex_multi_line):
    result, error = execute_query(complex_multi_line, sample_dataframes)

    assert error is None

    expected = (
      sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 25][
        ['name', 'age', 'id']
      ]
      .merge(
        sample_dataframes['orders'][sample_dataframes['orders']['amount'] > 100][
          ['amount', 'customer_id']
        ],
        left_on='id',
        right_on='customer_id',
      )
      .groupby('age')
      .agg('mean', numeric_only=True)
    )

    assert_frame_equal(result, expected)

  def test_invalid_multi_line(self, sample_dataframes):
    invalid_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, '&')])], True, {'nonexistent'}
    )

    result, error = execute_query(invalid_query, sample_dataframes)

    assert result is None

    assert error is not None
    assert 'KeyError' in error

  def test_multi_line_empty_result(self, sample_dataframes):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, '&')])], True, {'age'})

    result, error = execute_query(empty_query, sample_dataframes)

    assert error is None

    assert result is not None
    assert result.empty

  def test_modified_execute_query(self, sample_dataframes, complex_multi_line):
    single_line = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})

    result1, error1 = execute_query(single_line, sample_dataframes)

    assert error1 is None

    assert result1 is not None
    assert not result1.empty

    result2, error2 = execute_query(complex_multi_line, sample_dataframes)

    assert error2 is None

    assert result2 is not None
    assert not result2.empty
