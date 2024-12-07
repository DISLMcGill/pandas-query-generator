import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';

import { Navbar } from './components/navbar';
import { QueryResults } from './components/query-results';
import { SchemaDialog } from './components/schema-dialog';
import { SettingsDialog } from './components/settings-dialog';
import { usePersistedState } from './hooks/use-persisted-state';
import { usePyodideWorker } from './hooks/use-pyodide-worker';
import { useToast } from './hooks/use-toast';
import { EXAMPLE_SCHEMAS } from './lib/constants';
import { QueryStatistics, Settings } from './lib/types';

export const generateQueryGenerationCode = (
  schema: string,
  settings: Settings
) => `
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

queries, statistics = [str(query) for query in query_pool], query_pool.statistics()

json.dumps({
  'queries': queries,
  'statistics': {
    'execution_statistics': {
      'successful': statistics.execution_results.successful,
      'failed': statistics.execution_results.failed,
      'non_empty': statistics.execution_results.non_empty,
      'empty': statistics.execution_results.empty,
      'errors': statistics.execution_results.errors
    },
    'groupby_columns': statistics.groupby_columns,
    'merge_count': statistics.merge_count,
    'projection_columns': statistics.projection_columns,
    'queries_with_groupby': statistics.queries_with_groupby,
    'queries_with_merge': statistics.queries_with_merge,
    'queries_with_projection': statistics.queries_with_projection,
    'queries_with_selection': statistics.queries_with_selection,
    'query_structure': {
      'selection_probability': statistics.query_structure.selection_probability,
      'projection_probability': statistics.query_structure.projection_probability,
      'groupby_aggregation_probability': statistics.query_structure.groupby_aggregation_probability,
      'max_selection_conditions': statistics.query_structure.max_selection_conditions,
      'max_projection_columns': statistics.query_structure.max_projection_columns,
      'max_groupby_columns': statistics.query_structure.max_groupby_columns,
      'max_merges': statistics.query_structure.max_merges
    },
    'selection_conditions': statistics.selection_conditions,
    'total_queries': statistics.total_queries
  }
})
`;

const App = () => {
  const { runPython, loading, ready } = usePyodideWorker();

  const [generating, setGenerating] = useState(false);

  const [schema, setSchema] = usePersistedState<string>(
    'pqg-schema',
    JSON.stringify(EXAMPLE_SCHEMAS.tpch, null, 2)
  );

  const [selectedSchemaType, setSelectedSchemaType] = usePersistedState<string>(
    'pqg-schema-type',
    'tpch'
  );

  const [queries, setQueries] = useState<string[]>([]);

  const [statistics, setStatistics] = useState<QueryStatistics | undefined>(
    undefined
  );

  const { toast } = useToast();

  const [settings, setSettings] = usePersistedState<Settings>('pqg-settings', {
    enforceNonEmptyResults: false,
    groupbyProbability: 0.5,
    maxGroupbyColumns: 5,
    maxMerges: 2,
    maxProjectionColumns: 5,
    maxSelectionConditions: 5,
    multiLine: false,
    numQueries: 100,
    projectionProbability: 0.5,
    selectionProbability: 0.5,
  });

  const handleSettingChange = (setting: string, value: number | boolean) => {
    setSettings((prev) => ({
      ...prev,
      [setting]: value,
    }));
  };

  const handleSchemaChange = (newSchema: string, type: string) => {
    setSchema(newSchema);
    setSelectedSchemaType(type);
  };

  const generateQueries = async () => {
    setGenerating(true);

    try {
      const response = await runPython<{
        queries: string[];
        statistics: QueryStatistics;
      }>(generateQueryGenerationCode(schema, settings));
      setQueries(response.queries);
      setStatistics(response.statistics);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description:
          err instanceof Error ? err.message : 'Failed to generate queries',
      });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className='container mx-auto space-y-6 p-4'>
      <Navbar />
      <div className='grid grid-cols-2 gap-4'>
        <SchemaDialog
          schema={schema}
          selectedType={selectedSchemaType}
          onSchemaChange={handleSchemaChange}
        />
        <SettingsDialog
          settings={settings}
          onSettingChange={handleSettingChange}
        />
      </div>
      <Button
        className='w-full'
        size='lg'
        disabled={loading || generating || !ready}
        onClick={generateQueries}
      >
        {generating ? (
          <>
            <Loader2 className='mr-2 h-4 w-4 animate-spin' />
            Generating Queries...
          </>
        ) : (
          'Generate Queries'
        )}
      </Button>
      {queries.length > 0 && statistics !== undefined && (
        <QueryResults queries={queries} statistics={statistics} />
      )}
    </div>
  );
};

export default App;
