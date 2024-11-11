import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { Code2, Github, History, Loader2, Settings2 } from "lucide-react";
import { useToast } from "./hooks/use-toast";
import { Input } from "@/components/ui/input";
import { calculateMeanStd, cn, generatePyodideCode } from "./lib/utils";
import { ModeToggle } from "./components/mode-toggle";
import { EXAMPLE_SCHEMAS } from "./lib/constants";
import { QueryStatistics, Settings } from "./lib/types";
import { usePyodideClient } from "./hooks/use-pyodide-client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePersistedState } from "./hooks/use-persisted-state";

const Navbar = () => (
  <div className="flex items-center justify-between bg-card p-4">
    <div>
      <p className="font-semibold text-3xl">Pandas Query Generator 🐼</p>
      <p className="text-md text-muted-foreground">
        An interactive web demonstration
      </p>
    </div>
    <div className="flex items-center space-x-4">
      <Button variant="outline" size="icon" asChild>
        <a
          href="https://github.com/DISLMcGill/pandas-query-generator"
          target="_blank"
        >
          <Github className="h-4 w-4" />
        </a>
      </Button>
      <ModeToggle />
    </div>
  </div>
);

const SchemaSelector = ({
  selectedType,
  onSchemaSelect,
  className,
}: {
  selectedType: string;
  onSchemaSelect: (value: string, type: string) => void;
  className?: string;
}) => (
  <div className={cn("mb-4", className)}>
    <Select
      value={selectedType}
      onValueChange={(value) => {
        const selectedSchema = (EXAMPLE_SCHEMAS as any)[value];
        onSchemaSelect(JSON.stringify(selectedSchema, null, 2), value);
      }}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select example schema" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="tpch">TPC-H Schema</SelectItem>
        <SelectItem value="sports">Sports Schema</SelectItem>
        <SelectItem value="customer">Customer Schema</SelectItem>
      </SelectContent>
    </Select>
  </div>
);

const SchemaPanel = ({
  schema,
  selectedType,
  onSchemaChange,
}: {
  schema: string;
  selectedType: string;
  onSchemaChange: (schema: string, type: string) => void;
}) => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full">
          <Code2 className="mr-2 h-4 w-4" />
          Schema
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Schema Editor</span>
          </DialogTitle>
          <DialogDescription>
            Define your database schema in JSON format
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <SchemaSelector
            className="w-full mt-auto"
            selectedType={selectedType}
            onSchemaSelect={onSchemaChange}
          />
          <Textarea
            value={schema}
            onChange={(e) => onSchemaChange(e.target.value, selectedType)}
            className="font-mono min-h-[60vh]"
            placeholder="Enter your schema JSON here..."
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

const SettingsDialog = ({
  settings,
  onSettingChange,
}: {
  settings: Settings;
  onSettingChange: (setting: string, value: number) => void;
}) => (
  <Dialog>
    <DialogTrigger asChild>
      <Button variant="outline" className="w-full">
        <Settings2 className="mr-2 h-4 w-4" />
        Settings
      </Button>
    </DialogTrigger>
    <DialogContent className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Settings</DialogTitle>
        <DialogDescription>
          Customize the parameters for generating pandas queries
        </DialogDescription>
      </DialogHeader>
      <div className="grid gap-4 py-4">
        <div className="flex items-center space-x-2">
          <Label className="w-[200px]">Number of Queries</Label>
          <Input
            type="number"
            min={1}
            max={100000}
            value={settings.numQueries}
            onChange={(e) => {
              const value = parseInt(e.target.value);
              if (!isNaN(value) && value > 0 && value <= 100000) {
                onSettingChange("numQueries", value);
              }
            }}
            className="w-24"
          />
        </div>
        {[
          {
            name: "selectionProbability",
            label: "Selection Probability",
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: "projectionProbability",
            label: "Projection Probability",
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: "groupbyProbability",
            label: "Group By Probability",
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: "maxGroupbyColumns",
            label: "Max Group By Columns",
            min: 1,
            max: 10,
            step: 1,
          },
          {
            name: "maxMerges",
            label: "Max Merges",
            min: 1,
            max: 20,
            step: 1,
          },
          {
            name: "maxProjectionColumns",
            label: "Max Projection Columns",
            min: 1,
            max: 20,
            step: 1,
          },
          {
            name: "maxSelectionConditions",
            label: "Max Selection Conditions",
            min: 1,
            max: 20,
            step: 1,
          },
        ].map((slider) => (
          <div key={slider.name} className="flex items-center space-x-2">
            <Label className="w-[200px]">{slider.label}</Label>
            <div className="flex-1">
              <Slider
                min={slider.min}
                max={slider.max}
                step={slider.step}
                value={[settings[slider.name as keyof Settings]]}
                onValueChange={([value]) => onSettingChange(slider.name, value)}
              />
            </div>
            <span className="w-12 text-right">
              {settings[slider.name as keyof Settings]}
            </span>
          </div>
        ))}
      </div>
    </DialogContent>
  </Dialog>
);

const StatCard = ({
  title,
  children,
  className,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) => (
  <div className={cn("rounded-lg border p-4", className)}>
    <h3 className="font-semibold mb-2 text-lg flex items-center gap-2">
      {title}
    </h3>
    {children}
  </div>
);

const StatRow = ({
  label,
  value,
  target,
}: {
  label: string;
  value: string | number;
  target?: string | number;
  help?: string;
}) => (
  <div className="flex items-center justify-between py-1">
    <span className="text-muted-foreground">{label}</span>
    <div className="flex items-center gap-2">
      <span className="font-medium">{value}</span>
      {target && (
        <>
          <span className="text-muted-foreground">vs</span>
          <span className="text-muted-foreground">{target}</span>
        </>
      )}
    </div>
  </div>
);

const QueryStatisticsDisplay = ({
  statistics,
}: {
  statistics: QueryStatistics;
}) => {
  // Calculate statistics for operation counts
  const selectionStats = calculateMeanStd(statistics.selection_conditions);
  const projectionStats = calculateMeanStd(statistics.projection_columns);
  const groupByStats = calculateMeanStd(statistics.groupby_columns);
  const mergeStats = calculateMeanStd(statistics.merge_count);

  const getPercentage = (count: number) =>
    ((count / statistics.total_queries) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatCard title="Operation Frequencies">
          <div className="space-y-2">
            <StatRow
              label="Selection"
              value={`${getPercentage(statistics.queries_with_selection)}%`}
              target={`${(statistics.query_structure.selection_probability * 100).toFixed(1)}%`}
            />
            <StatRow
              label="Projection"
              value={`${getPercentage(statistics.queries_with_projection)}%`}
              target={`${(statistics.query_structure.projection_probability * 100).toFixed(1)}%`}
            />
            <StatRow
              label="Merge"
              value={`${getPercentage(statistics.queries_with_merge)}%`}
            />
            <StatRow
              label="Group By"
              value={`${getPercentage(statistics.queries_with_groupby)}%`}
              target={`${(statistics.query_structure.groupby_aggregation_probability * 100).toFixed(1)}%`}
            />
          </div>
        </StatCard>

        <StatCard title="Operation Counts">
          <div className="space-y-2">
            <StatRow
              label="Selection Conditions"
              value={`${selectionStats.mean.toFixed(1)} ± ${selectionStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_selection_conditions}
            />
            <StatRow
              label="Projection Columns"
              value={`${projectionStats.mean.toFixed(1)} ± ${projectionStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_projection_columns}
            />
            <StatRow
              label="Merges"
              value={`${mergeStats.mean.toFixed(1)} ± ${mergeStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_merges}
            />
            <StatRow
              label="Group By Columns"
              value={`${groupByStats.mean.toFixed(1)} ± ${groupByStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_groupby_columns}
            />
          </div>
        </StatCard>

        <StatCard title="Execution Results" className="md:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col items-center justify-center p-4 rounded-lg border bg-background">
              <div className="text-2xl font-bold">
                {statistics.total_queries}
              </div>
              <div className="text-sm text-muted-foreground text-center">
                Total Queries
              </div>
            </div>
            <div className="flex flex-col items-center justify-center p-4 rounded-lg border bg-background">
              <div className="text-2xl font-bold text-green-500">
                {(
                  (statistics.execution_results.successful /
                    statistics.total_queries) *
                  100
                ).toFixed(1)}
                %
              </div>
              <div className="text-sm text-muted-foreground text-center">
                Success Rate
              </div>
            </div>
            <div className="flex flex-col items-center justify-center p-4 rounded-lg border bg-background">
              <div className="text-2xl font-bold text-yellow-500">
                {(
                  (statistics.execution_results.empty /
                    statistics.total_queries) *
                  100
                ).toFixed(1)}
                %
              </div>
              <div className="text-sm text-muted-foreground text-center">
                Empty Result Sets
              </div>
            </div>
          </div>
          {Object.keys(statistics.execution_results.errors).length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Errors</h4>
              <div className="space-y-1">
                {Object.entries(statistics.execution_results.errors).map(
                  ([error, count]) => (
                    <div key={error} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{error}</span>
                      <span>{count}</span>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </StatCard>
      </div>
    </div>
  );
};

const QueryResults = ({
  queries,
  statistics,
}: {
  queries: string[];
  statistics: QueryStatistics;
}) => (
  <Tabs defaultValue="queries" className="w-full">
    <TabsList className="grid w-full grid-cols-2">
      <TabsTrigger value="queries">Generated Queries</TabsTrigger>
      <TabsTrigger value="stats">Statistics</TabsTrigger>
    </TabsList>
    <TabsContent value="queries">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code2 className="mr-2 h-4 w-4" />
            Generated Queries
            <span className="ml-2 text-sm text-muted-foreground">
              ({queries.length} queries)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] w-full rounded-md border p-4">
            <div className="space-y-6">
              {queries.map((query, index) => (
                <div key={index} className="font-mono text-sm">
                  <div className="text-muted-foreground mb-1">
                    Query {index + 1}:
                  </div>
                  <pre className="whitespace-pre-wrap break-words">{query}</pre>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </TabsContent>
    <TabsContent value="stats">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <History className="mr-2 h-4 w-4" />
            Query Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <QueryStatisticsDisplay statistics={statistics} />
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
);

const App = () => {
  const { client, loading } = usePyodideClient();

  const [generating, setGenerating] = useState(false);

  const [schema, setSchema] = usePersistedState<string>(
    "pqg-schema",
    JSON.stringify(EXAMPLE_SCHEMAS.tpch, null, 2),
  );

  const [selectedSchemaType, setSelectedSchemaType] = usePersistedState<string>(
    "pqg-schema-type",
    "tpch",
  );

  const [queries, setQueries] = useState<string[]>([]);
  const [statistics, setStatistics] = useState<QueryStatistics | undefined>(
    undefined,
  );

  const { toast } = useToast();

  const [settings, setSettings] = usePersistedState<Settings>("pqg-settings", {
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
      await new Promise((resolve) => setTimeout(resolve, 0));
      const result = client.runPython(generatePyodideCode(schema, settings));
      const { queries, stats } = result.toJs();
      setQueries(queries);
      setStatistics(stats);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description:
          err instanceof Error ? err.message : "Failed to generate queries",
      });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <Navbar />
      <div className="grid grid-cols-2 gap-4">
        <SchemaPanel
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
        className="w-full"
        size="lg"
        disabled={loading || generating || !client}
        onClick={generateQueries}
      >
        {generating ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generating Queries...
          </>
        ) : (
          "Generate Queries"
        )}
      </Button>
      {queries.length > 0 && statistics !== undefined && (
        <QueryResults queries={queries} statistics={statistics} />
      )}
    </div>
  );
};

export default App;
