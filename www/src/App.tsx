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
import { Github, Loader2 } from "lucide-react";
import { useToast } from "./hooks/use-toast";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Input } from "@/components/ui/input";
import { cn, generatePyodideCode } from "./lib/utils";
import { ModeToggle } from "./components/mode-toggle";
import { EXAMPLE_SCHEMAS } from "./lib/constants";
import { Settings } from "./lib/types";
import { usePyodideClient } from "./hooks/use-pyodide-client";

const Navbar = () => (
  <div className="flex items-center justify-between">
    <div className="m-4">
      <p className="font-semibold text-3xl text-center">
        Pandas Query Generator 🐼
      </p>
      <p className="text-xl italic">An interactive web demonstration</p>
    </div>
    <div className="flex items-center space-x-2">
      <a
        href="https://github.com/DISLMcGill/pandas-query-generator"
        target="_blank"
      >
        <Github />
      </a>
      <ModeToggle />
    </div>
  </div>
);

const SchemaSelector = ({
  onSchemaSelect,
  className,
}: {
  onSchemaSelect: (value: string) => void;
  className?: string;
}) => (
  <div className={cn("mb-4", className)}>
    <Select
      onValueChange={(value) => {
        const selectedSchema = (EXAMPLE_SCHEMAS as any)[value];
        onSchemaSelect(JSON.stringify(selectedSchema, null, 2));
      }}
      defaultValue="customer"
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select example schema" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="customer">Customer Schema</SelectItem>
        <SelectItem value="sports">Sports Schema</SelectItem>
        <SelectItem value="tpch">TPC-H Schema</SelectItem>
      </SelectContent>
    </Select>
  </div>
);

const SettingsSlider = ({
  name,
  value,
  onChange,
  min,
  max,
  step,
  label,
}: {
  name: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  label: string;
}) => (
  <div className="space-y-2 mb-4">
    <Label>{label}</Label>
    <div className="flex items-center gap-4">
      <Slider
        min={min}
        max={max}
        step={step}
        value={[value]}
        onValueChange={([value]) => onChange(value)}
        className="flex-grow"
      />
      <span className="w-12 text-right">{value}</span>
    </div>
  </div>
);

const SchemaPanel = ({
  schema,
  onSchemaChange,
}: {
  schema: string;
  onSchemaChange: (schema: string) => void;
}) => (
  <Card className="h-full border-0 rounded-none">
    <CardHeader>
      <CardTitle>Schema</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex flex-col">
        <SchemaSelector className="ml-auto" onSchemaSelect={onSchemaChange} />
        <Textarea
          value={schema}
          onChange={(e) => onSchemaChange(e.target.value)}
          className="font-mono min-h-[500px]"
          placeholder="Enter your schema JSON here..."
        />
      </div>
    </CardContent>
  </Card>
);

const SettingsPanel = ({
  settings,
  onSettingChange,
}: {
  settings: Settings;
  onSettingChange: (setting: string, value: number) => void;
}) => (
  <Card className="h-full border-0 rounded-none">
    <CardHeader>
      <CardTitle>Settings</CardTitle>
    </CardHeader>
    <CardContent className="space-y-6">
      <div className="flex items-center space-x-2">
        <Label>Number of Queries</Label>
        <div className="flex items-center space-x-2">
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
          <span className="text-sm text-muted-foreground">
            (min: 1, max: 100000)
          </span>
        </div>
      </div>
      <div className="space-y-4">
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
          <SettingsSlider
            key={slider.name}
            value={settings[slider.name as keyof Settings]}
            onChange={(value) => onSettingChange(slider.name, value)}
            {...slider}
          />
        ))}
      </div>
    </CardContent>
  </Card>
);

const ResultsPanel = ({
  queries,
  statistics,
}: {
  queries: string[];
  statistics: string;
}) => (
  <div className="rounded-lg border">
    <ResizablePanelGroup direction="horizontal" className="rounded-lg">
      <ResizablePanel defaultSize={50}>
        <Card className="h-full border-0 rounded-none">
          <CardContent>
            <Textarea
              value={queries.join("\n\n")}
              readOnly
              className="font-mono min-h-[350px] mt-6"
              placeholder="Generated queries will appear here..."
            />
          </CardContent>
        </Card>
      </ResizablePanel>
      <ResizableHandle />
      <ResizablePanel defaultSize={50}>
        <Card className="h-full border-0 rounded-none">
          <CardContent>
            <pre className="mt-2 text-sm whitespace-pre-wrap p-4 rounded-lg overflow-auto">
              {statistics}
            </pre>
          </CardContent>
        </Card>
      </ResizablePanel>
    </ResizablePanelGroup>
  </div>
);

const App = () => {
  const { client, loading } = usePyodideClient();

  const [generating, setGenerating] = useState(false);

  const [schema, setSchema] = useState<string>(
    JSON.stringify(EXAMPLE_SCHEMAS.customer, null, 2),
  );

  const [queries, setQueries] = useState<string[]>([]);
  const [statistics, setStatistics] = useState<string>("");

  const { toast } = useToast();

  const [settings, setSettings] = useState<Settings>({
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

  const generateQueries = async () => {
    if (!client) return;

    setGenerating(true);
    try {
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
    <div className="container mx-auto p-4 space-y-4">
      <Navbar />
      <div className="min-h-[600px] rounded-lg border">
        <ResizablePanelGroup direction="horizontal" className="rounded-lg">
          <ResizablePanel defaultSize={50}>
            <SchemaPanel schema={schema} onSchemaChange={setSchema} />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel defaultSize={50}>
            <SettingsPanel
              settings={settings}
              onSettingChange={handleSettingChange}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
      <div className="space-y-4">
        <Button
          className="w-full"
          disabled={loading || generating || !client}
          onClick={generateQueries}
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            "Generate Queries"
          )}
        </Button>
        {queries.length > 0 && (
          <ResultsPanel queries={queries} statistics={statistics} />
        )}
      </div>
    </div>
  );
};

export default App;
