from pandas_query_generator.group_by_aggregation import GroupByAggregation


class TestGroupByAggregation:
  def test_single_column_groupby(self):
    groupby = GroupByAggregation(['country'], 'mean')
    assert groupby.apply('customer') == ".groupby(by=['country']).agg('mean', numeric_only=True)"

  def test_multiple_columns_groupby(self):
    groupby = GroupByAggregation(['country', 'city'], 'mean')
    assert (
      groupby.apply('customer') == ".groupby(by=['country', 'city']).agg('mean', numeric_only=True)"
    )

  def test_count_aggregation(self):
    groupby = GroupByAggregation(['status'], 'count')
    assert groupby.apply('customer') == ".groupby(by=['status']).agg('count')"

  def test_different_aggregations(self):
    for agg in ['sum', 'min', 'max', 'mean']:
      groupby = GroupByAggregation(['country'], agg)
      expected = f".groupby(by=['country']).agg('{agg}'"
      expected += ', numeric_only=True)' if agg != 'count' else ')'
      assert groupby.apply('customer') == expected
