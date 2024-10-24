import pytest

from pandas_query_generator.group_by_aggregation import GroupByAggregation
from pandas_query_generator.merge import Merge
from pandas_query_generator.projection import Projection
from pandas_query_generator.query import Query
from pandas_query_generator.selection import Selection


# Test data
@pytest.fixture
def sample_entity():
  return 'customer'


@pytest.fixture
def simple_selection():
  return Selection([("'age'", '>=', 25, '&'), ("'status'", '==', "'active'", '|')])


@pytest.fixture
def simple_projection():
  return Projection(['name', 'age', 'email'])


@pytest.fixture
def simple_merge(simple_selection):
  nested_query = Query('orders', [simple_selection], False, {'age', 'status', 'order_id'})
  return Merge(nested_query, "'customer_id'", "'customer_id'")


@pytest.fixture
def simple_groupby():
  return GroupByAggregation(['country', 'city'], 'mean')


class TestQuery:
  def test_empty_query(self, sample_entity):
    query = Query(sample_entity, [], False, set())
    assert str(query) == 'customer'

  def test_single_operation_query(self, sample_entity, simple_selection):
    query = Query(sample_entity, [simple_selection], False, {'age', 'status'})
    expected = "customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
    assert str(query) == expected

  def test_multiple_operations_query(self, sample_entity, simple_selection, simple_projection):
    query = Query(
      sample_entity, [simple_selection, simple_projection], False, {'name', 'age', 'email'}
    )

    expected = (
      "customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
      + "[['name', 'age', 'email']]"
    )

    assert str(query) == expected

  def test_complex_query_with_merge(
    self, sample_entity, simple_selection, simple_merge, simple_projection
  ):
    query = Query(
      sample_entity,
      [simple_selection, simple_merge, simple_projection],
      False,
      {'name', 'age', 'email'},
    )

    expected = (
      "customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
      + ".merge(orders[(orders['age'] >= 25) & (orders['status'] == 'active')], "
      + "left_on='customer_id', right_on='customer_id')[['name', 'age', 'email']]"
    )

    assert str(query) == expected

  def test_query_with_groupby(self, sample_entity, simple_selection, simple_groupby):
    query = Query(sample_entity, [simple_selection, simple_groupby], False, {'country', 'city'})

    expected = (
      "customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
      + ".groupby(by=['country', 'city']).agg('mean', numeric_only=True)"
    )

    assert str(query) == expected

  def test_multiline_query_basic(self, sample_entity):
    query = Query(sample_entity, [Selection([("'age'", '>=', 25, '&')])], True, {'age'})
    result, counter = query.format_multi_line()
    expected = "df1 = customer[(customer['age'] >= 25)]"
    assert result == expected
    assert counter == 2

  def test_multiline_query_multiple_ops(self, sample_entity):
    query = Query(
      sample_entity,
      [
        Selection([("'age'", '>=', 25, '&')]),
        Projection(['name', 'email']),
        GroupByAggregation(['country'], 'mean'),
      ],
      True,
      {'name', 'email', 'country'},
    )

    result, counter = query.format_multi_line()

    expected_lines = [
      "df1 = customer[(customer['age'] >= 25)]",
      "df2 = df1[['name', 'email']]",
      "df3 = df2.groupby(by=['country']).agg('mean', numeric_only=True)",
    ]

    assert result == '\n'.join(expected_lines)
    assert counter == 4

  def test_multiline_query_with_merge(self, sample_entity):
    right_query = Query(
      'orders', [Selection([("'status'", '==', "'active'", '&')])], False, {'status'}
    )

    query = Query(
      sample_entity,
      [Selection([("'age'", '>=', 25, '&')]), Merge(right_query, "'customer_id'", "'customer_id'")],
      True,
      {'age', 'customer_id'},
    )

    result, counter = query.format_multi_line()

    expected_lines = [
      "df1 = customer[(customer['age'] >= 25)]",
      "df2 = orders[(orders['status'] == 'active')]",
      "df3 = df1.merge(df2, left_on='customer_id', right_on='customer_id')",
    ]

    assert result == '\n'.join(expected_lines)
    assert counter == 4

  def test_multiline_nested_merges(self, sample_entity):
    inner_query = Query(
      'orders', [Selection([("'status'", '==', "'pending'", '&')])], False, {'status'}
    )

    middle_query = Query(
      'products', [Merge(inner_query, "'order_id'", "'order_id'")], False, {'order_id'}
    )

    query = Query(
      sample_entity,
      [
        Selection([("'active'", '==', 'True', '&')]),
        Merge(middle_query, "'product_id'", "'product_id'"),
      ],
      True,
      {'active', 'product_id'},
    )

    result, counter = query.format_multi_line()

    expected_lines = [
      "df1 = customer[(customer['active'] == True)]",
      "df2 = orders[(orders['status'] == 'pending')]",
      "df3 = products.merge(df2, left_on='order_id', right_on='order_id')",
      "df4 = df1.merge(df3, left_on='product_id', right_on='product_id')",
    ]

    assert result == '\n'.join(expected_lines)
    assert counter == 5

  def test_query_sorting(self, sample_entity):
    simple_query = Query(sample_entity, [], False, set())

    single_merge = Query(
      sample_entity, [Merge(Query('orders', [], False, set()), "'id'", "'id'")], False, {'id'}
    )

    nested_merge = Query(
      sample_entity,
      [
        Merge(
          Query('orders', [Merge(Query('items', [], False, set()), "'id'", "'id'")], False, {'id'}),
          "'id'",
          "'id'",
        )
      ],
      False,
      {'id'},
    )

    queries = [nested_merge, simple_query, single_merge]
    sorted_queries = sorted(queries)

    assert sorted_queries == [simple_query, single_merge, nested_merge]
    assert sorted_queries[0].complexity < sorted_queries[1].complexity
    assert sorted_queries[1].complexity < sorted_queries[2].complexity

  def test_query_deduplication(self, sample_entity, simple_selection):
    query1 = Query(sample_entity, [simple_selection], False, {'age', 'status'})
    query2 = Query(sample_entity, [simple_selection], False, {'age', 'status'})

    query3 = Query(sample_entity, [simple_selection], True, {'age', 'status'})

    queries = {query1, query2, query3}

    assert len(queries) == 2

    expected_single_line = "customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
    expected_multi_line = (
      "df1 = customer[(customer['age'] >= 25) & (customer['status'] == 'active')]"
    )

    result_strings = {str(q) for q in queries}

    assert expected_single_line in result_strings
    assert expected_multi_line in result_strings
