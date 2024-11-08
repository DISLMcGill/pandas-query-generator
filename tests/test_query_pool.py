import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from pandas_query_generator.arguments import QueryFilter
from pandas_query_generator.group_by_aggregation import GroupByAggregation
from pandas_query_generator.merge import Merge
from pandas_query_generator.projection import Projection
from pandas_query_generator.query import Query
from pandas_query_generator.query_pool import QueryPool
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
  def test_empty_pool(self, sample_dataframes):
    pool = QueryPool([])
    results = pool.execute(sample_dataframes)
    assert results == []
    assert pool._results == []

  def test_simple_selection(self, sample_dataframes, simple_selection):
    pool = QueryPool([simple_selection])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

    assert error is None

    expected = sample_dataframes['customers'][sample_dataframes['customers']['age'] >= 30]

    assert_frame_equal(result, expected)

  def test_simple_projection(self, sample_dataframes, simple_projection):
    pool = QueryPool([simple_projection])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

    assert error is None

    expected = sample_dataframes['customers'][['name', 'age']]

    assert_frame_equal(result, expected)

  def test_simple_groupby(self, sample_dataframes, simple_groupby):
    pool = QueryPool([simple_groupby])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

    assert error is None

    expected = sample_dataframes['customers'].groupby('country').agg('count')

    assert_frame_equal(result, expected)

  def test_simple_merge(self, sample_dataframes, simple_merge):
    pool = QueryPool([simple_merge])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

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

    pool = QueryPool([bad_query])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

    assert result is None
    assert error is not None
    assert 'KeyError' in error

  def test_empty_result(self, sample_dataframes):
    query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})

    pool = QueryPool([query])
    results = pool.execute(sample_dataframes)

    assert len(results) == 1
    result, error = results[0]

    assert error is None
    assert result is not None
    assert result.empty


class TestQueryPoolFilter:
  def test_non_empty_filter(self, sample_dataframes, simple_selection, simple_projection):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})
    pool = QueryPool([simple_selection, empty_query, simple_projection])
    pool.filter(sample_dataframes, QueryFilter.NON_EMPTY)

    assert len(pool.queries) == 2
    assert pool.queries == [simple_selection, simple_projection]

  def test_empty_filter(self, sample_dataframes, simple_selection):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, '&')])], False, {'age'})
    pool = QueryPool([simple_selection, empty_query])
    pool.filter(sample_dataframes, QueryFilter.EMPTY)

    assert len(pool.queries) == 1
    assert pool.queries == [empty_query]

  def test_error_filter(self, sample_dataframes, simple_selection):
    bad_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, '&')])], False, {'nonexistent'}
    )

    pool = QueryPool([simple_selection, bad_query])
    pool.filter(sample_dataframes, QueryFilter.HAS_ERROR)

    assert len(pool.queries) == 1
    assert pool.queries == [bad_query]


class TestQueryPoolStatistics:
  def test_empty_pool_statistics(self):
    pool = QueryPool([])
    stats = pool.calculate_statistics()

    assert stats.total_queries == 0
    assert stats.avg_operations_per_query == 0.0
    assert stats.avg_merge_count == 0.0
    assert stats.avg_selection_conditions == 0.0
    assert stats.avg_projection_columns == 0.0
    assert stats.avg_groupby_columns == 0.0
    assert stats.max_merge_depth == 0
    assert stats.max_merge_chain == 0
    assert len(stats.operations) == 0

  def test_operation_counting(
    self, simple_selection, simple_projection, simple_groupby, simple_merge
  ):
    pool = QueryPool([simple_selection, simple_projection, simple_groupby, simple_merge])
    stats = pool.calculate_statistics()

    assert stats.total_queries == 4
    assert stats.operations['Selection'] == 1
    assert stats.operations['Projection'] == 1
    assert stats.operations['GroupByAggregation'] == 1
    assert stats.operations['Merge'] == 1

    assert stats.avg_operations_per_query == 1.0
    assert stats.avg_merge_count == 0.25
    assert stats.avg_selection_conditions == 1.0
    assert stats.avg_projection_columns == 2.0
    assert stats.avg_groupby_columns == 1.0

  def test_merge_depth_statistics(self):
    innermost_query = Query('items', [], False, set())

    inner_merge = Query(
      'orders', [Merge(innermost_query, "'order_id'", "'item_id'")], False, {'order_id', 'item_id'}
    )

    outer_query = Query(
      'customers',
      [Merge(inner_merge, "'customer_id'", "'order_id'")],
      False,
      {'customer_id', 'order_id'},
    )

    pool = QueryPool([outer_query])
    stats = pool.calculate_statistics()

    assert stats.max_merge_depth == 2
    assert stats.max_merge_chain == 2
    assert stats.avg_merge_count == 2.0

  def test_complex_query_statistics(self):
    nested_query = Query(
      'orders',
      [
        Selection([("'status'", '==', "'active'", '&')]),
        Projection(['order_id', 'amount', 'status']),
      ],
      False,
      {'order_id', 'amount', 'status'},
    )

    complex_query = Query(
      'customers',
      [
        Selection(
          [
            ("'age'", '>=', 30, '&'),
            ("'country'", '==', "'US'", '&'),
            ("'status'", '==', "'active'", '|'),
          ]
        ),
        Merge(nested_query, "'id'", "'customer_id'"),
        Projection(['name', 'age', 'country', 'amount']),
        GroupByAggregation(['country', 'status'], 'mean'),
      ],
      False,
      {'name', 'age', 'country', 'amount', 'status'},
    )

    pool = QueryPool([complex_query])
    stats = pool.calculate_statistics()

    assert stats.total_queries == 1
    assert stats.avg_operations_per_query == 4.0
    assert stats.avg_merge_count == 1.0
    assert stats.avg_selection_conditions == 3.0
    assert stats.avg_projection_columns == 4.0
    assert stats.avg_groupby_columns == 2.0
    assert stats.max_merge_depth == 1
    assert stats.max_merge_chain == 1

  def test_multiple_queries_statistics(self):
    query1 = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})

    query2 = Query(
      'customers', [Projection(['name', 'age', 'country'])], False, {'name', 'age', 'country'}
    )

    query3 = Query(
      'orders',
      [
        Selection([("'amount'", '>', 100, '&'), ("'status'", '==', "'pending'", '|')]),
        Projection(['order_id', 'amount']),
      ],
      False,
      {'order_id', 'amount', 'status'},
    )

    pool = QueryPool([query1, query2, query3])
    stats = pool.calculate_statistics()

    assert stats.total_queries == 3
    assert stats.avg_operations_per_query == 4 / 3
    assert stats.avg_merge_count == 0.0
    assert stats.avg_selection_conditions == 1.5
    assert stats.avg_projection_columns == 2.5
    assert stats.max_merge_depth == 0
    assert stats.max_merge_chain == 0

  def test_execution_statistics(self, sample_dataframes, simple_selection):
    pool = QueryPool([simple_selection])
    pool.execute(sample_dataframes)
    stats = pool.calculate_statistics()

    assert stats.execution_results.successful_executions == 1
    assert stats.execution_results.failed_executions == 0
    assert stats.execution_results.success_rate == 100.0

  def test_error_tracking(self, sample_dataframes):
    bad_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, '&')])], False, {'nonexistent'}
    )

    pool = QueryPool([bad_query])
    pool.execute(sample_dataframes)
    stats = pool.calculate_statistics()

    assert stats.execution_results.failed_executions == 1
    assert stats.execution_results.successful_executions == 0
    assert stats.execution_results.success_rate == 0.0
    assert len(stats.execution_results.errors) > 0


class TestQueryPoolSort:
  def test_sort_empty_pool(self):
    pool = QueryPool([])
    pool.sort()
    assert pool.queries == []
    assert pool._results == []

  def test_sort_without_results(self, simple_selection, simple_merge):
    pool = QueryPool([simple_merge, simple_selection])
    pool.sort()
    assert pool.queries == [simple_selection, simple_merge]
    assert pool.queries[0].complexity < pool.queries[1].complexity

  def test_sort_with_results(self, sample_dataframes, simple_selection, simple_merge):
    pool = QueryPool([simple_merge, simple_selection])

    pool.execute(sample_dataframes)

    result_data = [(r[0].copy() if r[0] is not None else None, r[1]) for r in pool._results]

    pool.sort()

    assert pool.queries == [simple_selection, simple_merge]
    assert len(pool._results) == 2

    for original, current in zip(result_data, pool._results):
      if original[0] is not None and current[0] is not None:
        assert_frame_equal(original[0], current[0])
      assert original[1] == current[1]

  def test_deduplication_without_results(self, simple_selection):
    duplicate_query = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})

    pool = QueryPool([simple_selection, duplicate_query, simple_selection])
    pool.sort()

    assert len(pool.queries) == 1
    assert pool.queries[0] == simple_selection

  def test_deduplication_with_results(self, sample_dataframes, simple_selection):
    duplicate_query = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})

    pool = QueryPool([simple_selection, duplicate_query])

    results = pool.execute(sample_dataframes)
    assert all(error is None for _, error in results)

    pool._results[1] = (None, 'Test error')

    pool.sort()

    assert len(pool.queries) == 1
    assert len(pool._results) == 1
    assert pool._results[0][1] is None

  def test_multiline_distinction(self):
    single_line = Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'})

    multi_line = Query('customers', [Selection([("'age'", '>=', 30, '&')])], True, {'age'})

    pool = QueryPool([single_line, multi_line])
    pool.sort()

    assert len(pool.queries) == 2
    assert str(pool.queries[0]) != str(pool.queries[1])

  def test_complex_deduplication(self, sample_dataframes, simple_selection):
    duplicates = [
      Query('customers', [Selection([("'age'", '>=', 30, '&')])], False, {'age'}) for _ in range(3)
    ]

    pool = QueryPool([simple_selection] + duplicates)
    pool.execute(sample_dataframes)

    pool._results[1] = (None, 'Error 1')
    pool._results[2] = (None, 'Error 2')

    pool.sort()

    assert len(pool.queries) == 1
    assert len(pool._results) == 1
    assert pool._results[0][1] is None
