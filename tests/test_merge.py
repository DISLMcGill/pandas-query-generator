import pytest

from pandas_query_generator.merge import Merge
from pandas_query_generator.projection import Projection
from pandas_query_generator.query import Query
from pandas_query_generator.selection import Selection


@pytest.fixture
def simple_selection():
  return Selection([("'age'", '>=', 25, '&'), ("'status'", '==', "'active'", '|')])


@pytest.fixture
def simple_projection():
  return Projection(['name', 'age', 'email'])


@pytest.fixture
def simple_merge(simple_selection):
  nested_query = Query('orders', [simple_selection], False)
  return Merge(nested_query, 'customer_id', 'customer_id')


class TestMerge:
  def test_simple_merge(self, simple_merge):
    expected = ".merge(orders[(orders['age'] >= 25) & (orders['status'] == 'active')], left_on='customer_id', right_on='customer_id')"
    assert simple_merge.apply('customer') == expected

  def test_merge_with_complex_right_query(self, simple_projection):
    nested_query = Query('orders', [simple_projection], False)
    merge = Merge(nested_query, 'customer_id', 'order_id')
    expected = (
      ".merge(orders[['name', 'age', 'email']], left_on='customer_id', right_on='order_id')"
    )
    assert merge.apply('customer') == expected
