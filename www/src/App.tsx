import { loadPyodide, PyodideInterface } from "pyodide";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { useToast } from "./hooks/use-toast";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

const sampleSchema = {
  entities: {
    customer: {
      primary_key: "C_CUSTKEY",
      properties: {
        C_CUSTKEY: {
          type: "int",
          min: 1,
          max: 1000,
        },
        C_NAME: {
          type: "string",
          starting_character: ["A", "B", "C"],
        },
        C_STATUS: {
          type: "enum",
          values: ["active", "inactive"],
        },
      },
      foreign_keys: {},
    },
    order: {
      primary_key: "O_ORDERKEY",
      properties: {
        O_ORDERKEY: {
          type: "int",
          min: 1,
          max: 5000,
        },
        O_CUSTKEY: {
          type: "int",
          min: 1,
          max: 1000,
        },
        O_TOTALPRICE: {
          type: "float",
          min: 10.0,
          max: 1000.0,
        },
        O_ORDERSTATUS: {
          type: "enum",
          values: ["pending", "completed", "cancelled"],
        },
      },
      foreign_keys: {
        O_CUSTKEY: ["C_CUSTKEY", "customer"],
      },
    },
  },
};

const App = () => {
  const [client, setClient] = useState<PyodideInterface | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [schema, setSchema] = useState(JSON.stringify(sampleSchema, null, 2));
  const [queries, setQueries] = useState<string[]>([]);

  const { toast } = useToast();

  const [settings, setSettings] = useState({
    selectionProbability: 0.7,
    projectionProbability: 0.7,
    groupbyProbability: 0.3,
    maxGroupbyColumns: 3,
    maxMerges: 10,
    maxProjectionColumns: 5,
    maxSelectionConditions: 10,
  });

  useEffect(() => {
    setLoading(true);

    loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.3/full",
    }).then(async (pyodide: PyodideInterface) => {
      try {
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install("pqg");
        setClient(pyodide);
      } catch (err) {
        toast({
          variant: "destructive",
          title: "Error",
          description:
            err instanceof Error ? err.message : "Failed to load Python client",
        });
      } finally {
        setLoading(false);
      }
    });
  }, [toast]);

  const generateQueries = async () => {
    if (!client) return;

    setGenerating(true);

    try {
      const generator = client.runPython(`
import json

from pandas_query_generator import Generator
from pandas_query_generator import QueryStructure
from pandas_query_generator import Schema

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

[str(query) for query in generator.generate(10)]
`);

      setQueries(generator.toJs());
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

  const handleSettingChange = (setting: string, value: number) => {
    setSettings((prev) => ({
      ...prev,
      [setting]: value,
    }));
  };

  const renderSlider = (
    name: string,
    min: number,
    max: number,
    step: number,
    label: string,
  ) => (
    <div className="space-y-2 mb-4">
      <Label>{label}</Label>
      <div className="flex items-center gap-4">
        <Slider
          min={min}
          max={max}
          step={step}
          value={[settings[name as keyof typeof settings]]}
          onValueChange={([value]) => handleSettingChange(name, value)}
          className="flex-grow"
        />
        <span className="w-12 text-right">
          {settings[name as keyof typeof settings]}
        </span>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-4 space-y-4">
      <p className="font-semibold text-3xl text-center">
        Pandas Query Generator 🐼
      </p>
      <p className="italic text-xl text-center">
        An interactive web demonstration
      </p>

      <div className="min-h-[600px] rounded-lg border">
        <ResizablePanelGroup direction="horizontal" className="rounded-lg">
          <ResizablePanel defaultSize={50}>
            <div className="h-full">
              <Card className="h-full border-0 rounded-none">
                <CardHeader>
                  <CardTitle>Schema</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={schema}
                    onChange={(e) => setSchema(e.target.value)}
                    className="font-mono min-h-[500px]"
                    placeholder="Enter your schema JSON here..."
                  />
                </CardContent>
              </Card>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          <ResizablePanel defaultSize={50}>
            <div className="h-full">
              <Card className="h-full border-0 rounded-none">
                <CardHeader>
                  <CardTitle>Query Structure</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    {renderSlider(
                      "selectionProbability",
                      0,
                      1,
                      0.1,
                      "Selection Probability",
                    )}
                    {renderSlider(
                      "projectionProbability",
                      0,
                      1,
                      0.1,
                      "Projection Probability",
                    )}
                    {renderSlider(
                      "groupbyProbability",
                      0,
                      1,
                      0.1,
                      "Group By Probability",
                    )}
                  </div>
                  <div className="space-y-4">
                    {renderSlider(
                      "maxGroupbyColumns",
                      1,
                      10,
                      1,
                      "Max Group By Columns",
                    )}
                    {renderSlider("maxMerges", 1, 20, 1, "Max Merges")}
                    {renderSlider(
                      "maxProjectionColumns",
                      1,
                      20,
                      1,
                      "Max Projection Columns",
                    )}
                    {renderSlider(
                      "maxSelectionConditions",
                      1,
                      20,
                      1,
                      "Max Selection Conditions",
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
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
          <Card>
            <CardHeader>
              <CardTitle>Generated Queries</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                value={queries.join("\n\n")}
                readOnly
                className="font-mono h-[200px]"
                placeholder="Generated queries will appear here..."
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default App;
