import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';

import { Navbar } from './components/navbar';
import { QueryResults } from './components/query-results';
import { SchemaDialog } from './components/schema-dialog';
import { SettingsDialog } from './components/settings-dialog';
import { usePersistedState } from './hooks/use-persisted-state';
import { usePyodideClient } from './hooks/use-pyodide-client';
import { useToast } from './hooks/use-toast';
import { EXAMPLE_SCHEMAS } from './lib/constants';
import { QueryStatistics, Settings } from './lib/types';

const App = () => {
  const { runPython, loading } = usePyodideClient();

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
    selectionProbability: 0.5,
    projectionProbability: 0.5,
    groupbyProbability: 0.5,
    maxGroupbyColumns: 5,
    maxMerges: 2,
    maxProjectionColumns: 5,
    maxSelectionConditions: 5,
    numQueries: 100,
    multiLine: false,
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

  const pythonCode = `
import json, sys

from pqg import Generator, QueryStructure, Schema, QueryPool

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
query_pool = generator.generate(${settings.numQueries}, multi_line=${settings.multiLine ? 'True' : 'False'}, multi_processing=False)
query_pool.sort()

{ 'queries': [str(query) for query in query_pool], 'stats': query_pool.statistics() }
  `;

  const generateQueries = async () => {
    setGenerating(true);

    try {
      const result = await runPython<{
        queries: string[];
        stats: QueryStatistics;
      }>(pythonCode);
      setQueries(result.queries);
      setStatistics(result.stats);
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
        disabled={loading || generating}
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
