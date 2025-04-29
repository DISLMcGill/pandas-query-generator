import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from pqg.arguments import QueryFilter
from pqg.group_by_aggregation import GroupByAggregation
from pqg.merge import Merge
from pqg.projection import Projection
from pqg.query import Query
from pqg.query_pool import QueryPool
from pqg.query_structure import QueryStructure
from pqg.selection import Selection


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
  return Query('customers', [Selection([("'age'", '>=', 30, None)])], False, {'age'})


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
      [Selection([("'nonexistent_column'", '>=', 30, None)])],
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
    query = Query('customers', [Selection([("'age'", '>', 100, None)])], False, {'age'})

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
    empty_query = Query('customers', [Selection([("'age'", '>', 100, None)])], False, {'age'})

    pool = QueryPool(
      [simple_selection, empty_query, simple_projection], query_structure, sample_dataframes
    )

    pool.filter(QueryFilter.NON_EMPTY)

    assert len(pool._queries) == 2
    assert pool._queries == [simple_selection, simple_projection]

  def test_empty_filter(self, sample_dataframes, query_structure, simple_selection):
    empty_query = Query('customers', [Selection([("'age'", '>', 100, None)])], False, {'age'})

    pool = QueryPool([simple_selection, empty_query], query_structure, sample_dataframes)
    pool.filter(QueryFilter.EMPTY)

    assert len(pool._queries) == 1
    assert pool._queries == [empty_query]

  def test_error_filter(self, sample_dataframes, query_structure, simple_selection):
    bad_query = Query(
      'customers', [Selection([("'nonexistent'", '>=', 30, None)])], False, {'nonexistent'}
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
    single_line = Query('customers', [Selection([("'age'", '>=', 30, None)])], False, {'age'})
    multi_line = Query('customers', [Selection([("'age'", '>=', 30, None)])], True, {'age'})

    pool = QueryPool([single_line, multi_line], query_structure, sample_dataframes)
    pool.sort()

    assert len(pool._queries) == 2
    assert str(pool._queries[0]) != str(pool._queries[1])


class TestQueryPoolStatistics:
  def test_empty_pool_statistics(self, sample_dataframes, query_structure):
    pool = QueryPool([], query_structure, sample_dataframes)
    stats = pool.statistics()

    assert stats.total_queries == 0
    assert stats.queries_with_selection == 0
    assert stats.queries_with_projection == 0
    assert stats.queries_with_groupby == 0
    assert stats.queries_with_merge == 0
    assert len(stats.selection_conditions) == 0
    assert len(stats.projection_columns) == 0
    assert len(stats.groupby_columns) == 0
    assert len(stats.merge_count) == 0

  def test_basic_operation_frequencies(
    self,
    sample_dataframes,
    query_structure,
    simple_selection,
    simple_projection,
    simple_groupby,
    simple_merge,
  ):
    pool = QueryPool(
      [simple_selection, simple_projection, simple_groupby, simple_merge],
      query_structure,
      sample_dataframes,
    )
    stats = pool.statistics()

    assert stats.total_queries == 4
    assert stats.queries_with_selection == 1
    assert stats.queries_with_projection == 1
    assert stats.queries_with_groupby == 1
    assert stats.queries_with_merge == 1

    assert stats.selection_conditions == [1]
    assert stats.projection_columns == [2]
    assert stats.groupby_columns == [1]
    assert stats.merge_count == [1]

  def test_execution_statistics(
    self,
    sample_dataframes,
    query_structure,
    simple_selection,
    simple_projection,
  ):
    bad_query = Query(
      'customers',
      [Selection([("'nonexistent'", '>=', 30, None)])],
      False,
      {'nonexistent'},
    )

    empty_query = Query(
      'customers',
      [Selection([("'age'", '>', 100, None)])],
      False,
      {'age'},
    )

    pool = QueryPool(
      [simple_selection, simple_projection, bad_query, empty_query],
      query_structure,
      sample_dataframes,
    )

    stats = pool.statistics()

    assert stats.execution_results.successful == 3
    assert stats.execution_results.failed == 1
    assert stats.execution_results.non_empty == 2
    assert stats.execution_results.empty == 1

    assert len(stats.execution_results.errors) == 1
    assert "KeyError: 'nonexistent'" in stats.execution_results.errors

  def test_complex_query_statistics(self, sample_dataframes, query_structure):
    complex_query = Query(
      'customers',
      [
        Selection(
          [
            ("'age'", '>=', 30, '&'),
            ("'country'", '==', "'US'", None),
          ]
        ),
        Projection(['name', 'age', 'country']),
      ],
      False,
      {'age', 'country', 'name'},
    )

    pool = QueryPool([complex_query], query_structure, sample_dataframes)
    stats = pool.statistics()

    assert stats.queries_with_selection == 1
    assert stats.queries_with_projection == 1
    assert stats.selection_conditions == [2]
    assert stats.projection_columns == [3]

  def test_nested_merge_statistics(self, sample_dataframes, query_structure):
    inner_query = Query('orders', [], False, set())

    outer_query = Query(
      'customers',
      [
        Merge(inner_query, "'id'", "'customer_id'"),
        Merge(inner_query, "'id'", "'customer_id'"),
      ],
      False,
      {'id', 'customer_id'},
    )

    pool = QueryPool([outer_query], query_structure, sample_dataframes)
    stats = pool.statistics()

    assert stats.queries_with_merge == 1
    assert stats.merge_count == [2]

  def test_statistics_match_structure(self, sample_dataframes, query_structure):
    complex_query = Query(
      'customers',
      [
        Selection(
          [
            ("'age'", '>=', 30, '&'),
            ("'country'", '==', "'US'", None),
          ]
        ),
        Projection(['name', 'age', 'country']),
        GroupByAggregation(['country'], 'mean'),
      ],
      False,
      {'age', 'country', 'name'},
    )

    pool = QueryPool([complex_query], query_structure, sample_dataframes)
    stats = pool.statistics()

    assert max(stats.selection_conditions) <= query_structure.max_selection_conditions
    assert max(stats.projection_columns) <= query_structure.max_projection_columns
    assert max(stats.groupby_columns) <= query_structure.max_groupby_columns


class TestQueryPoolDeduplicate:
  def test_deduplicate_without_results(self, sample_dataframes, query_structure):
    # Create duplicate queries with same operations
    selection = Selection([("'age'", '>=', 30, '&')])
    query1 = Query('customers', [selection], False, {'age'})
    query2 = Query('customers', [selection], False, {'age'})
    query3 = Query('customers', [selection], True, {'age'})  # Multi-line version

    pool = QueryPool([query1, query2, query3], query_structure, sample_dataframes)
    initial_length = len(pool)

    pool.deduplicate()

    assert len(pool) == 2  # Should keep one single-line and one multi-line
    assert pool._queries[0].multi_line != pool._queries[1].multi_line
    assert len(pool._results) == 0  # No results yet
    assert initial_length == 3

  def test_deduplicate_with_results(self, sample_dataframes, query_structure):
    # Create duplicate queries
    selection = Selection([("'age'", '>=', 30, '&')])
    query1 = Query('customers', [selection], False, {'age'})
    query2 = Query('customers', [selection], False, {'age'})
    query3 = Query('customers', [Selection([("'age'", '>=', 25, '&')])], False, {'age'})

    pool = QueryPool([query1, query2, query3], query_structure, sample_dataframes)
    pool.execute()  # Generate results
    initial_results = len(pool._results)

    pool.deduplicate()

    assert len(pool) == 2  # Should keep unique queries only
    assert len(pool._results) == 2  # Results should match queries
    assert initial_results == 3

    for _, (result, error) in pool.items():
      assert result is not None or error is not None

  def test_deduplicate_with_different_complexity(self, sample_dataframes, query_structure):
    simple_selection = Selection([("'age'", '>=', 30, '&')])

    complex_selection = Selection([("'age'", '>=', 30, '&'), ("'country'", '==', "'US'", '&')])

    query1 = Query('customers', [simple_selection], False, {'age'})
    query2 = Query('customers', [simple_selection], False, {'age'})
    query3 = Query('customers', [complex_selection], False, {'age', 'country'})

    pool = QueryPool([query1, query2, query3], query_structure, sample_dataframes)
    pool.execute()

    pool.deduplicate()

    assert len(pool) == 2  # Should keep one simple and one complex query
    assert pool._queries[0].complexity < pool._queries[1].complexity

  def test_deduplicate_empty_pool(self, sample_dataframes, query_structure):
    pool = QueryPool([], query_structure, sample_dataframes)
    pool.deduplicate()

    assert len(pool) == 0
    assert len(pool._results) == 0

  def test_deduplicate_all_unique(self, sample_dataframes, query_structure):
    queries = [
      Query('customers', [Selection([("'age'", '>=', i, '&')])], False, {'age'}) for i in range(3)
    ]

    pool = QueryPool(queries, query_structure, sample_dataframes)
    pool.execute()

    initial_length = len(pool)

    pool.deduplicate()

    assert len(pool) == initial_length
    assert len(pool._results) == initial_length
    assert all(q.columns == {'age'} for q in pool._queries)

  def test_deduplicate_maintains_query_result_pairs(self, sample_dataframes, query_structure):
    selection1 = Selection([("'age'", '>=', 30, '&')])
    selection2 = Selection([("'age'", '<', 25, '&')])

    queries = [
      Query('customers', [selection1], False, {'age'}),
      Query('customers', [selection1], False, {'age'}),
      Query('customers', [selection2], False, {'age'}),
    ]

    pool = QueryPool(queries, query_structure, sample_dataframes)

    results = pool.execute()
    assert len(results) == 3

    gte_30_result = next(
      result for query, result in zip(queries, results) if "'age' >= 30" in str(query)
    )

    lt_25_result = next(
      result for query, result in zip(queries, results) if "'age' < 25" in str(query)
    )

    pool.deduplicate()

    assert len(pool._queries) == 2
    assert len(pool._results) == 2

    remaining_queries = set()

    for query, result in pool.items():
      if "'age' >= 30" in str(query):
        remaining_queries.add('gte_30')
        pd.testing.assert_frame_equal(result[0], gte_30_result[0])
        assert result[0] is not None
        assert all(result[0]['age'] >= 30)
      elif "'age' < 25" in str(query):
        remaining_queries.add('lt_25')
        pd.testing.assert_frame_equal(result[0], lt_25_result[0])
        assert result[0] is not None
        assert all(result[0]['age'] < 25)

    assert remaining_queries == {'gte_30', 'lt_25'}, f'Found queries: {remaining_queries}'
