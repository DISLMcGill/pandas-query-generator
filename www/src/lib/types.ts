export type ExecutionStatistics = {
  successful: number;
  failed: number;
  non_empty: number;
  empty: number;
  errors: Record<string, number>;
};

export type Settings = {
  selectionProbability: number;
  projectionProbability: number;
  groupbyProbability: number;
  maxGroupbyColumns: number;
  maxMerges: number;
  maxProjectionColumns: number;
  maxSelectionConditions: number;
  numQueries: number;
  multiLine: boolean;
};

export type QueryStatistics = {
  query_structure: {
    selection_probability: number;
    projection_probability: number;
    groupby_aggregation_probability: number;
    max_selection_conditions: number;
    max_projection_columns: number;
    max_groupby_columns: number;
    max_merges: number;
  };
  total_queries: number;
  queries_with_selection: number;
  queries_with_projection: number;
  queries_with_groupby: number;
  queries_with_merge: number;
  selection_conditions: number[];
  projection_columns: number[];
  groupby_columns: number[];
  merge_count: number[];
  execution_results: ExecutionStatistics;
};
