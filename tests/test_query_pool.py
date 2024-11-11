import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from pandas_query_generator.arguments import QueryFilter
from pandas_query_generator.group_by_aggregation import GroupByAggregation
from pandas_query_generator.merge import Merge
from pandas_query_generator.projection import Projection
from pandas_query_generator.query import Query
from pandas_query_generator.query_pool import QueryPool
from pandas_query_generator.query_structure import QueryStructure
from pandas_query_generator.selection import Selection


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
def query_structure():
  """Basic query structure configuration for testing."""
  return QueryStructure(
    groupby_aggregation_probability=0.5,
    max_groupby_columns=3,
    max_merges=2,
    max_projection_columns=5,
    max_selection_conditions=3,
    projection_probability=0.5,
    selection_probability=0.5,
  )


@pytest.fixture
def simple_selection():
  return Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})


@pytest.fixture
def simple_projection():
  return Query('customers', [Projection(['name', 'age'])], False, {'name', 'age'})


@pytest.fixture
def simple_groupby():
  return Query('customers', [GroupByAggregation(['country'], 'count')], False, {'country'})


@pytest.fixture
def simple_merge():
  nested_query = Query('orders', [], False, set())

  return Query(
    'customers', [Merge(nested_query, "'id'", "'customer_id'")], False, {'id', 'customer_id'}
  )


class TestQueryPoolExecution:
  def test_empty_pool(self, sample_dataframes, query_structure):
    pool = QueryPool([], query_structure, sample_dataframes)
    results = pool.execute()

    assert results == []
    assert len(list(pool.items())) == 0
    assert pool._results == []

  def test_simple_selection(self, sample_dataframes, query_structure, simple_selection):
    pool = QueryPool([simple_selection], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert error is None

    expected = sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 30]

    assert_frame_equal(result, expected)

  def test_simple_projection(self, sample_dataframes, query_structure, simple_projection):
    pool = QueryPool([simple_projection], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert error is None

    expected = sample_dataframes['customers'][['name', 'age']]

    assert_frame_equal(result, expected)

  def test_simple_groupby(self, sample_dataframes, query_structure, simple_groupby):
    pool = QueryPool([simple_groupby], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert error is None

    expected = sample_dataframes['customers'].groupby('country').agg('count')

    assert_frame_equal(result, expected)

  def test_simple_merge(self, sample_dataframes, query_structure, simple_merge):
    pool = QueryPool([simple_merge], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert error is None

    expected = sample_dataframes['customers'].merge(
      sample_dataframes['orders'], left_on='id', right_on='customer_id'
    )

    assert_frame_equal(result, expected)

  def test_invalid_query(self, sample_dataframes, query_structure):
    bad_query = Query(
      'customers',
      [Selection([("'nonexistent_column'", '>=', 30, '&')])],
      False,
      {'nonexistent_column'},
    )

    pool = QueryPool([bad_query], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert result is None
    assert error is not None
    assert 'KeyError' in error

  def test_empty_result(self, sample_dataframes, query_structure):
    query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})

    pool = QueryPool([query], query_structure, sample_dataframes)
    results = pool.execute()

    assert len(results) == 1

    result, error = results[0]
    assert error is None
    assert result is not None
    assert result.empty


class TestQueryPoolFilter:
  def test_non_empty_filter(
    self, sample_dataframes, query_structure, simple_selection, simple_projection
  ):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})

    pool = QueryPool(
      [simple_selection, empty_query, simple_projection], query_structure, sample_dataframes
    )

    pool.filter(QueryFilter.NON_EMPTY)

    assert len(pool._queries) == 2
    assert pool._queries == [simple_selection, simple_projection]

  def test_empty_filter(self, sample_dataframes, query_structure, simple_selection):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})

    pool = QueryPool([simple_selection, empty_query], query_structure, sample_dataframes)
    pool.filter(QueryFilter.EMPTY)

    assert len(pool._queries) == 1
    assert pool._queries == [empty_query]

  def test_error_filter(self, sample_dataframes, query_structure, simple_selection):
    bad_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, '&')])], False, {'nonexistent'}
    )

    pool = QueryPool([simple_selection, bad_query], query_structure, sample_dataframes)
    pool.filter(QueryFilter.HAS_ERROR)

    assert len(pool._queries) == 1
    assert pool._queries == [bad_query]


class TestQueryPoolSort:
  def test_sort_empty_pool(self, query_structure, sample_dataframes):
    pool = QueryPool([], query_structure, sample_dataframes)
    pool.sort()

    assert pool._queries == []
    assert pool._results == []

  def test_sort_without_results(
    self, sample_dataframes, query_structure, simple_selection, simple_merge
  ):
    pool = QueryPool([simple_merge, simple_selection], query_structure, sample_dataframes)
    pool.sort()

    assert pool._queries == [simple_selection, simple_merge]
    assert pool._queries[0].complexity < pool._queries[1].complexity

  def test_sort_with_results(
    self, sample_dataframes, query_structure, simple_selection, simple_merge
  ):
    pool = QueryPool([simple_merge, simple_selection], query_structure, sample_dataframes)
    pool.execute()

    query_to_result = {str(query): result for query, result in pool.items()}

    pool.sort()

    assert pool._queries == [simple_selection, simple_merge]
    assert len(pool._results) == 2

    for query, current_result in zip(pool._queries, pool._results):
      original_result = query_to_result[str(query)]

      if original_result[0] is not None and current_result[0] is not None:
        assert_frame_equal(original_result[0], current_result[0])

      assert original_result[1] == current_result[1]

  def test_multiline_distinction(self, sample_dataframes, query_structure):
    single_line = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})
    multi_line = Query('customers', [Selection([("'age'", '>=', 30, '&')])], True, {'age'})

    pool = QueryPool([single_line, multi_line], query_structure, sample_dataframes)
    pool.sort()

    assert len(pool._queries) == 2
    assert str(pool._queries[0]) != str(pool._queries[1])
