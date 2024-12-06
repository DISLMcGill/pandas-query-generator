import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { Settings } from './types';

export const calculateMeanStd = (values: number[]) => {
  if (values.length === 0) return { mean: 0, std: 0, max: 0 };

  const mean = values.reduce((a, b) => a + b) / values.length;

  const variance =
    values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (values.length - 1);

  const std = values.length > 1 ? Math.sqrt(variance) : 0;

  const max = Math.max(...values);

  return { mean, std, max };
};

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const generatePyodideCode = (schema: string, settings: Settings) => `
import json, sys

from pqg import Generator, QueryStructure, Schema, QueryPool, GenerateOptions

schema = Schema.from_dict(json.loads('''${schema}'''))

query_structure = QueryStructure(
  groupby_aggregation_probability=${settings.groupbyProbability},
  max_groupby_columns=${settings.maxGroupbyColumns},
  max_merges=${settings.maxMerges},
  max_projection_columns=${settings.maxProjectionColumns},
  max_selection_conditions=${settings.maxSelectionConditions},
  projection_probability=${settings.projectionProbability},
  selection_probability=${settings.selectionProbability}
)

generator = Generator(schema, query_structure)

generate_options = GenerateOptions(
  ensure_non_empty=${settings.enforceNonEmptyResults ? 'True' : 'False'},
  multi_line=${settings.multiLine ? 'True' : 'False'},
  multi_processing=False,
  num_queries=${settings.numQueries}
)

query_pool = generator.generate(generate_options)

query_pool.sort()

{ 'queries': [str(query) for query in query_pool], 'stats': query_pool.statistics() }
`;
