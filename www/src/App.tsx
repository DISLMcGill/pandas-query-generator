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
import { generatePyodideCode } from './lib/utils';

const App = () => {
  const { client, loading } = usePyodideClient();

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
  });

  const handleSettingChange = (setting: string, value: number) => {
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
    if (!client) return;

    setGenerating(true);

    try {
      // This is a hack to get the loading indicator to show
      await new Promise((resolve) => setTimeout(resolve, 0));

      // TODO: Run this in a web worker
      const result = client.runPython(generatePyodideCode(schema, settings));

      const { queries, stats } = result.toJs();
      setQueries(queries);
      setStatistics(stats);
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
        disabled={loading || generating || !client}
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
