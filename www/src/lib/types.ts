export type ExecutionStatistics = {
  successful: number;
  failed: number;
  non_empty: number;
  empty: number;
  errors: Record<string, number>;
};

export type Settings = {
  enforceNonEmptyResults: boolean;
  groupbyProbability: number;
  maxGroupbyColumns: number;
  maxMerges: number;
  maxProjectionColumns: number;
  maxSelectionConditions: number;
  multiLine: boolean;
  numQueries: number;
  projectionProbability: number;
  selectionProbability: number;
};

export type QueryStatistics = {
  execution_statistics: ExecutionStatistics;
  groupby_columns: number[];
  merge_count: number[];
  projection_columns: number[];
  queries_with_groupby: number;
  queries_with_merge: number;
  queries_with_projection: number;
  queries_with_selection: number;
  query_structure: QueryStructure;
  selection_conditions: number[];
  total_queries: number;
};

type QueryStructure = {
  selection_probability: number;
  projection_probability: number;
  groupby_aggregation_probability: number;
  max_selection_conditions: number;
  max_projection_columns: number;
  max_groupby_columns: number;
  max_merges: number;
};
