import { loadPyodide, PyodideInterface } from "pyodide";
import { useEffect, useState } from "react";
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
import { cn } from "./lib/utils";
import { ModeToggle } from "./components/mode-toggle";

const exampleSchemas = {
  sports: {
    entities: {
      team: {
        properties: {
          T_TEAMKEY: { type: "string", starting_character: ["t"] },
          T_GROUP: {
            type: "enum",
            values: ["a", "b", "c", "d", "e", "f", "g", "h"],
          },
          T_PLAYERCOUNT: { type: "int", min: 18, max: 26 },
        },
        primary_key: "T_TEAMKEY",
      },
      association: {
        properties: {
          A_ASSOCKEY: { type: "string", starting_character: ["f"] },
          A_TEAMKEY: { type: "string", starting_character: ["t"] },
          A_FOUNDEDYEAR: { type: "int", min: 1900, max: 2000 },
          A_PRESIDENT: { type: "string", starting_character: ["p"] },
        },
        primary_key: "A_ASSOCKEY",
        foreign_keys: {
          A_TEAMKEY: ["T_TEAMKEY", "team"],
        },
      },
      coach: {
        properties: {
          C_COACHKEY: { type: "int", min: 1, max: 100 },
          C_ROLE: {
            type: "enum",
            values: [
              "head coach",
              "assistant coach",
              "goalkeeper coach",
              "fitness coach",
            ],
          },
          C_TEAMKEY: { type: "string", starting_character: ["t"] },
          C_NAME: { type: "string", starting_character: ["c"] },
          C_EXPYEARS: { type: "int", min: 1, max: 40 },
        },
        primary_key: ["C_COACHKEY", "C_TEAMKEY"],
        foreign_keys: {
          C_TEAMKEY: ["T_TEAMKEY", "team"],
        },
      },
      stadium: {
        properties: {
          S_STADIUMKEY: { type: "int", min: 1, max: 12 },
          S_NAME: { type: "string", starting_character: ["s"] },
          S_CITY: { type: "string", starting_character: ["d", "a", "l", "r"] },
          S_LOCATION: {
            type: "string",
            starting_character: ["n", "s", "e", "w", "c"],
          },
          S_CAPACITY: { type: "int", min: 40000, max: 90000 },
          S_YEARBUILT: { type: "int", min: 1950, max: 2022 },
        },
        primary_key: "S_STADIUMKEY",
      },
      match: {
        properties: {
          M_MATCHKEY: { type: "int", min: 1, max: 64 },
          M_TEAM1KEY: { type: "string", starting_character: ["t"] },
          M_TEAM2KEY: { type: "string", starting_character: ["t"] },
          M_STADIUMKEY: { type: "int", min: 1, max: 12 },
          M_DATE: { type: "date", min: "2022-11-20", max: "2022-12-18" },
          M_TIME: { type: "string", starting_character: ["1", "2"] },
          M_DURATION: { type: "int", min: 90, max: 150 },
          M_ROUND: {
            type: "enum",
            values: [
              "group stage",
              "round of 16",
              "quarter-final",
              "semi-final",
              "final",
            ],
          },
          M_SCORE1: { type: "int", min: 0, max: 7 },
          M_SCORE2: { type: "int", min: 0, max: 7 },
          M_ATTENDANCE: { type: "int", min: 30000, max: 90000 },
        },
        primary_key: "M_MATCHKEY",
        foreign_keys: {
          M_TEAM1KEY: ["T_TEAMKEY", "team"],
          M_TEAM2KEY: ["T_TEAMKEY", "team"],
          M_STADIUMKEY: ["S_STADIUMKEY", "stadium"],
        },
      },
    },
  },
  tpch: {
    entities: {
      customer: {
        properties: {
          C_CUSTKEY: { type: "int", min: 1, max: 100 },
          C_NAME: { type: "string", starting_character: ["C"] },
          C_ADDRESS: {
            type: "string",
            starting_character: [
              "I",
              "H",
              "X",
              "s",
              "9",
              "n",
              "z",
              "K",
              "T",
              "u",
              "Q",
              "O",
              "7",
            ],
          },
          C_NATIONKEY: { type: "int", min: 0, max: 23 },
          C_PHONE: {
            type: "string",
            starting_character: [
              "1",
              "2",
              "3",
              "25-",
              "13-",
              "27-",
              "18-",
              "22-",
            ],
          },
          C_ACCTBAL: { type: "float", min: -917.25, max: 9983.38 },
          MKTSEGMENT: {
            type: "enum",
            values: [
              "BUILDING",
              "AUTOMOBILE",
              "MACHINERY",
              "HOUSEHOLD",
              "FURNITURE",
            ],
          },
          C_COMMENT: {
            type: "string",
            starting_character: ["i", "s", "l", "r", "c", "t", "e"],
          },
        },
        primary_key: "C_CUSTKEY",
        foreign_keys: {
          C_NATIONKEY: ["N_NATIONKEY", "nation"],
        },
      },
      lineitem: {
        properties: {
          L_ORDERKEY: { type: "int", min: 1, max: 194 },
          L_PARTKEY: { type: "int", min: 450, max: 198344 },
          L_SUPPKEY: { type: "int", min: 22, max: 9983 },
          LINENUMBER: { type: "int", min: 1, max: 7 },
          QUANTITY: { type: "int", min: 1, max: 50 },
          EXTENDEDPRICE: { type: "float", min: 1606.52, max: 88089.08 },
          DISCOUNT: { type: "float", min: 0.0, max: 0.1 },
          TAX: { type: "float", min: 0.0, max: 0.08 },
          RETURNFLAG: { type: "enum", values: ["N", "R", "A"] },
          LINESTATUS: { type: "enum", values: ["O", "F"] },
          SHIPDATE: { type: "date", min: "1992-04-27", max: "1998-10-30" },
          COMMITDATE: { type: "date", min: "1992-05-15", max: "1998-10-16" },
          RECEIPTDATE: { type: "date", min: "1992-05-02", max: "1998-11-06" },
          SHIPINSTRUCT: {
            type: "enum",
            values: [
              "DELIVER IN PERSON",
              "TAKE BACK RETURN",
              "NONE",
              "COLLECT COD",
            ],
          },
          SHIPMODE: {
            type: "enum",
            values: ["TRUCK", "MAIL", "REG AIR", "AIR", "FOB", "RAIL", "SHIP"],
          },
        },
        primary_key: ["L_ORDERKEY", "L_PARTKEY", "L_SUPPKEY"],
        foreign_keys: {
          L_ORDERKEY: ["O_ORDERKEY", "orders"],
          L_PARTKEY: ["PS_PARTKEY", "partsupp"],
          L_SUPPKEY: ["PS_SUPPKEY", "partsupp"],
        },
      },
      nation: {
        properties: {
          N_NATIONKEY: { type: "int", min: 0, max: 24 },
          N_NAME: {
            type: "string",
            starting_character: [
              "I",
              "A",
              "C",
              "E",
              "J",
              "M",
              "R",
              "U",
              "B",
              "F",
              "G",
              "K",
              "P",
              "S",
              "V",
            ],
          },
          N_REGIONKEY: { type: "int", min: 0, max: 4 },
          N_COMMENT: {
            type: "string",
            starting_character: [" ", "y", "e", "r", "s", "a", "v", "l"],
          },
        },
        primary_key: "N_NATIONKEY",
        foreign_keys: {
          N_REGIONKEY: ["R_REGIONKEY", "region"],
        },
      },
      orders: {
        properties: {
          O_ORDERKEY: { type: "int", min: 1, max: 800 },
          O_CUSTKEY: { type: "int", min: 302, max: 149641 },
          ORDERSTATUS: { type: "enum", values: ["O", "F", "P"] },
          TOTALPRICE: { type: "float", min: 1156.67, max: 355180.76 },
          ORDERDATE: { type: "date", min: "1992-01-13", max: "1998-07-21" },
          ORDERPRIORITY: {
            type: "enum",
            values: [
              "1-URGENT",
              "2-HIGH",
              "3-MEDIUM",
              "4-NOT SPECIFIED",
              "5-LOW",
            ],
          },
          CLERK: { type: "string", starting_character: ["C"] },
          SHIPPRIORITY: { type: "int", min: 0, max: 0 },
        },
        primary_key: "O_ORDERKEY",
        foreign_keys: {
          O_CUSTKEY: ["C_CUSTKEY", "customer"],
        },
      },
      part: {
        properties: {
          P_PARTKEY: { type: "int", min: 1, max: 200 },
          P_NAME: {
            type: "string",
            starting_character: ["b", "s", "l", "c", "m", "p", "g", "t"],
          },
          MFGR: {
            type: "enum",
            values: [
              "Manufacturer#1",
              "Manufacturer#2",
              "Manufacturer#3",
              "Manufacturer#4",
              "Manufacturer#5",
            ],
          },
          BRAND: {
            type: "enum",
            values: [
              "Brand#13",
              "Brand#42",
              "Brand#34",
              "Brand#32",
              "Brand#24",
            ],
          },
          TYPE: {
            type: "string",
            starting_character: ["S", "M", "E", "P", "L", "STA", "SMA"],
          },
          SIZE: { type: "int", min: 1, max: 49 },
          CONTAINER: {
            type: "string",
            starting_character: ["JUMBO", "LG", "WRAP", "MED", "SM"],
          },
          RETAILPRICE: { type: "float", min: 901.0, max: 1100.2 },
        },
        primary_key: "P_PARTKEY",
      },
      partsupp: {
        properties: {
          PS_PARTKEY: { type: "int", min: 1, max: 50 },
          PS_SUPPKEY: { type: "int", min: 2, max: 7551 },
          AVAILQTY: { type: "int", min: 43, max: 9988 },
          SUPPLYCOST: { type: "float", min: 14.78, max: 996.12 },
        },
        primary_key: ["PS_PARTKEY", "PS_SUPPKEY"],
        foreign_keys: {
          PS_PARTKEY: ["P_PARTKEY", "part"],
          PS_SUPPKEY: ["S_SUPPKEY", "supplier"],
        },
      },
      region: {
        properties: {
          R_REGIONKEY: { type: "int", min: 0, max: 4 },
          R_NAME: {
            type: "string",
            starting_character: ["A", "E", "M", "AFR", "AME", "ASI"],
          },
          R_COMMENT: {
            type: "string",
            starting_character: ["l", "h", "g", "u"],
          },
        },
        primary_key: "R_REGIONKEY",
      },
      supplier: {
        properties: {
          S_SUPPKEY: { type: "int", min: 1, max: 200 },
          S_NAME: { type: "string", starting_character: ["S"] },
          S_ADDRESS: {
            type: "string",
            starting_character: ["N", "e", "f", "J", "o", "c", "b", "u"],
          },
          S_NATIONKEY: { type: "int", min: 0, max: 24 },
          S_PHONE: {
            type: "string",
            starting_character: [
              "1",
              "2",
              "3",
              "28-",
              "32-",
              "26-",
              "14-",
              "17-",
            ],
          },
          S_ACCTBAL: { type: "float", min: -966.2, max: 9915.24 },
        },
        primary_key: "S_SUPPKEY",
        foreign_keys: {
          S_NATIONKEY: ["N_NATIONKEY", "nation"],
        },
      },
    },
  },
  customer: {
    entities: {
      customer: {
        primary_key: "C_CUSTKEY",
        properties: {
          C_CUSTKEY: { type: "int", min: 1, max: 1000 },
          C_NAME: { type: "string", starting_character: ["A", "B", "C"] },
          C_STATUS: { type: "enum", values: ["active", "inactive"] },
        },
        foreign_keys: {},
      },
      order: {
        primary_key: "O_ORDERKEY",
        properties: {
          O_ORDERKEY: { type: "int", min: 1, max: 5000 },
          O_CUSTKEY: { type: "int", min: 1, max: 1000 },
          O_TOTALPRICE: { type: "float", min: 10.0, max: 1000.0 },
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
  },
};

const SchemaSelector = ({
  onSchemaSelect,
  className,
}: {
  onSchemaSelect: (value: string) => void;
  className?: string;
}) => {
  const handleSchemaChange = (value: string) => {
    const selectedSchema = (exampleSchemas as any)[value];
    onSchemaSelect(JSON.stringify(selectedSchema, null, 2));
  };

  return (
    <div className={cn("mb-4", className)}>
      <Select onValueChange={handleSchemaChange} defaultValue="customer">
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
};

const App = () => {
  const [client, setClient] = useState<PyodideInterface | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [schema, setSchema] = useState<string>(
    JSON.stringify(exampleSchemas.customer, null, 2),
  );
  const [queries, setQueries] = useState<string[]>([]);
  const [statistics, setStatistics] = useState<string>("");

  const { toast } = useToast();

  const [settings, setSettings] = useState({
    selectionProbability: 0.5,
    projectionProbability: 0.5,
    groupbyProbability: 0.5,
    maxGroupbyColumns: 5,
    maxMerges: 2,
    maxProjectionColumns: 5,
    maxSelectionConditions: 5,
    numQueries: 100,
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
      const result = client.runPython(`
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

{
  'queries': [str(query) for query in query_pool],
  'stats': str(query_pool.statistics())
}
`);

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

      <div className="min-h-[600px] rounded-lg border">
        <ResizablePanelGroup direction="horizontal" className="rounded-lg">
          <ResizablePanel defaultSize={50}>
            <div className="h-full">
              <Card className="h-full border-0 rounded-none">
                <CardHeader>
                  <CardTitle>Schema</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col">
                    <SchemaSelector
                      className="ml-auto"
                      onSchemaSelect={(value) => setSchema(value)}
                    />
                    <Textarea
                      value={schema}
                      onChange={(e) => setSchema(e.target.value)}
                      className="font-mono min-h-[600px]"
                      placeholder="Enter your schema JSON here..."
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          <ResizablePanel defaultSize={50}>
            <div className="h-full">
              <Card className="h-full border-0 rounded-none">
                <CardHeader>
                  <CardTitle>Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label>Number of Queries</Label>
                    <div className="flex items-center space-x-2">
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        value={settings.numQueries}
                        onChange={(e) => {
                          const value = parseInt(e.target.value);
                          if (!isNaN(value) && value > 0 && value <= 100000) {
                            handleSettingChange("numQueries", value);
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
          <div className="rounded-lg border">
            <ResizablePanelGroup direction="horizontal" className="rounded-lg">
              <ResizablePanel defaultSize={50}>
                <div className="h-full">
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
                </div>
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel defaultSize={50}>
                <div className="h-full">
                  <Card className="h-full border-0 rounded-none">
                    <CardContent>
                      <pre className="mt-2 text-sm whitespace-pre-wrap p-4 rounded-lg overflow-auto">
                        {statistics}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
