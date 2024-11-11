import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Settings } from "./types";

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
import sys
sys.modules['_multiprocessing'] = object

import json

from pandas_query_generator import Generator
from pandas_query_generator import QueryStructure
from pandas_query_generator import Schema
from pandas_query_generator import QueryPool

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
query_pool = generator.generate(${settings.numQueries}, multi_processing=False)
query_pool.sort()

{ 'queries': [str(query) for query in query_pool], 'stats': query_pool.statistics() }
`;
