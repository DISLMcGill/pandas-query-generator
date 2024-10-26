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
  """Create sample DataFrames for testing."""
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
    """Test that selection query executes correctly."""
    result, error = execute_query(simple_selection, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 30]
    assert_frame_equal(result, expected)

  def test_simple_projection(self, sample_dataframes, simple_projection):
    """Test that projection query executes correctly."""
    result, error = execute_query(simple_projection, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'][['name', 'age']]
    assert_frame_equal(result, expected)

  def test_simple_groupby(self, sample_dataframes, simple_groupby):
    """Test that groupby query executes correctly."""
    result, error = execute_query(simple_groupby, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'].groupby('country').agg('count')
    assert_frame_equal(result, expected)

  def test_simple_merge(self, sample_dataframes, simple_merge):
    """Test that merge query executes correctly."""
    result, error = execute_query(simple_merge, sample_dataframes)
    assert error is None
    expected = sample_dataframes['customers'].merge(
      sample_dataframes['orders'], left_on='id', right_on='customer_id'
    )
    assert_frame_equal(result, expected)

  def test_invalid_query(self, sample_dataframes):
    """Test handling of invalid query."""
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
    """Test handling of query that produces empty result."""
    query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})
    result, error = execute_query(query, sample_dataframes)
    assert result is not None
    assert error is None
    assert result.empty


class TestGenerateQueryStatistics:
  def test_empty_queries(self):
    """Test statistics generation for empty query list."""
    stats = generate_query_statistics([])
    assert stats['total_queries'] == 0
    assert stats['avg_operations_per_query'] == 0.0
    assert len(stats['operations']) == 0

  def test_query_type_counting(
    self, simple_selection, simple_projection, simple_groupby, simple_merge
  ):
    """Test counting different types of operations."""
    queries = [simple_selection, simple_projection, simple_groupby, simple_merge]
    stats = generate_query_statistics(queries)

    assert stats['total_queries'] == 4
    assert stats['operations']['Selection'] == 1
    assert stats['operations']['Projection'] == 1
    assert stats['operations']['GroupByAggregation'] == 1
    assert stats['operations']['Merge'] == 1

  def test_execution_results(self, sample_dataframes, simple_selection):
    """Test statistics generation with execution results."""
    result, error = execute_query(simple_selection, sample_dataframes)
    stats = generate_query_statistics([simple_selection], [(result, error)])

    assert stats['execution_results']['successful_executions'] == 1
    assert stats['execution_results']['failed_executions'] == 0
    assert stats['execution_results']['success_rate'] == 100.0

  def test_error_tracking(self, sample_dataframes):
    """Test tracking of execution errors."""
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
    """Test aggregation of query statistics."""
    # Create a more complex merge query
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
    assert stats['merges'][0] == 1  # One merge with 0 operations
    assert stats['merges'][2] == 1  # One merge with 2 operations
    assert stats['selections'][1] == 1  # One selection with 1 condition
    assert stats['avg_operations_per_query'] > 0
