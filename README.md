## Pandas Query Generator 🐼

**Pandas Query Generator (pqg)** is a tool designed to help users generate
synthetic [pandas](https://pandas.pydata.org/) queries for training machine
learning models that estimate query execution costs or predict cardinality.
The binary is called **pqg** and has only been tested on a unix-based system.

## Installation

You can install the query generator using [pip](https://pip.pypa.io/en/stable/installation/), the Python package manager:

```bash
pip install pqg
```

Alternatively, you can use the local web playground:

```
cd www && bun install && bunx --bun vite
```

*n.b.* This command will require you to have [bun](https://bun.sh/) installed on your machine.

This will spin up a development server at `localhost:5173` where you can interact with the playground.
You can upload your schemas, tweak query parameters and generate queries.

## Usage

The query generator exposes both a command-line tool and library interface.

### CLI

Below is the standard output of `pqg --help`, which elaborates on the various
command-line arguments the tool accepts:

```present uv run pqg --help
usage: pqg [--disable-multi-processing] [--filter] [--groupby-aggregation-probability] [--max-groupby-columns] [--max-merges] [--max-projection-columns] [--max-selection-conditions] [--multi-line] --num-queries [--output-file] [--projection-probability] --schema [--selection-probability] [--sort] [--verbose]

Pandas Query Generator CLI

options:
  -h --help Show this help message and exit
  --disable-multi-processing Generate and execute queries in a consecutive fashion (default: False)
  --filter Filter generated queries by specific criteria
  --groupby-aggregation-probability Probability of including groupby aggregation operations (default: 0.5)
  --max-groupby-columns Maximum number of columns in group by operations (default: 5)
  --max-merges Maximum number of table merges allowed (default: 2)
  --max-projection-columns Maximum number of columns to project (default: 5)
  --max-selection-conditions Maximum number of conditions in selection operations (default: 5)
  --multi-line Format queries on multiple lines (default: False)
  --num-queries num_queries The number of queries to generate
  --output-file The name of the file to write the results to (default: queries.txt)
  --projection-probability Probability of including projection operations (default: 0.5)
  --schema schema Path to the relational schema JSON file
  --selection-probability Probability of including selection operations (default: 0.5)
  --sort Whether or not to sort the queries by complexity (default: False)
  --verbose Print extra generation information and statistics (default: False)
```

The required options, as shown, are `--num-queries` and `--schema`. The
`--num-queries` option simply instructs the program to generate a certain amount
of queries.

The `--schema` option is a pointer to a JSON file path that describes
meta-information about the data we're generating queries for.

A sample schema looks like this:

```json
{
  "entities": {
    "customer": {
      "primary_key": "C_CUSTKEY",
      "properties": {
        "C_CUSTKEY": { "type": "int", "min": 1, "max": 1000 },
        "C_NAME": { "type": "string", "starting_character": ["A", "B", "C"] },
        "C_STATUS": { "type": "enum", "values": ["active", "inactive"] }
      },
      "foreign_keys": {}
    },
    "order": {
      "primary_key": "O_ORDERKEY",
      "properties": {
        "O_ORDERKEY": { "type": "int", "min": 1, "max": 5000 },
        "O_CUSTKEY": { "type": "int", "min": 1, "max": 1000 },
        "O_TOTALPRICE": { "type": "float", "min": 10.0, "max": 1000.0 },
        "O_ORDERSTATUS": { "type": "enum", "values": ["pending", "completed", "cancelled"] }
      },
      "foreign_keys": {
        "O_CUSTKEY": ["C_CUSTKEY", "customer"]
      }
    }
  }
}
```

This file can be found in `/examples/customer/schema.json`, generate a few
queries from this schema with `pqg --num-queries 100 --schema examples/customer/schema.json --verbose`.

Schemas for these files can be found in their respective directories within
`/examples`.

### Library

We expose various structures that make it easy to generate queries fast:

```python
import json

from pandas_query_generator import Generator, Schema, QueryStructure, QueryPool,
QueryFilter

# Assumes `schema.json` exists and conforms to the schema format
schema = Schema.from_file('schema.json')

query_structure = QueryStructure(
  groupby_aggregation_probability=0.5,
  max_groupby_columns=4,
  max_merges=10,
  max_projection_columns=5,
  max_selection_conditions=10,
  projection_probability=0.5,
  selection_probability=0.5
)

generator = Generator(schema, query_structure)

# Generate 1000 queries
query_pool = generator.generate(1000)

# Filter out queries with non-empty result sets
query_pool.filter(QueryFilter.NON_EMPTY)

# Sort queries by complexity
query_pool.sort()

for query in query_pool:
  print(query)
```

Comprehensive API documentation is generated using the `sphinx` Python package.
You can generate the documentation using the following command in the project
root:

```bash
cd docs && make html
```

...then serve it with:

```bash
python3 -m http.server 8000 --directory docs/build/html
```

This will spin up a server at `http://localhost:8000`, open it up in your
preferred browser to view the documentation.

## How does it work?

Check out the paper in the `/docs` folder for more information!

## Prior Art

This version of the Pandas Query Generator is based off of the thorough research
work of previous students of
[COMP 400](https://www.mcgill.ca/study/2023-2024/courses/comp-400) at
[McGill University](https://www.mcgill.ca/), namely Edge Satir, Hongxin Huo and
Dailun Li.
