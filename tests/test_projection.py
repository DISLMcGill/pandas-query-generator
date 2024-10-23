from pandas_query_generator.projection import Projection


class TestProjection:
  def test_empty_projection(self):
    projection = Projection([])
    assert projection.apply('customer') == '[[]]'

  def test_single_column_projection(self):
    projection = Projection(['name'])
    assert projection.apply('customer') == "[['name']]"

  def test_multiple_columns_projection(self):
    projection = Projection(['name', 'age', 'email'])
    assert projection.apply('customer') == "[['name', 'age', 'email']]"
