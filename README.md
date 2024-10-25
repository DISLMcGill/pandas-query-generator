## Pandas Query Generator 🐼

**Pandas Query Generator (pqg)** is a tool designed to help users generate
synthetic [pandas](https://pandas.pydata.org/) queries for training machine
learning models that estimate query execution costs or predict cardinality.

### Installation

You can install the query generator using [pip](https://pip.pypa.io/en/stable/installation/), the Python package manager:

```bash
pip install pqg
```

### Usage

Below is the standard output of `pqg --help`, which elaborates on the various
command-line arguments the tool accepts:

```present uv run pqg --help
usage: pqg [--max-groupby-columns] [--max-merges] [--max-projection-columns] [--max-selection-conditions] [--multi-line] --num-queries [--output-file] --schema [--sorted] [--verbose]

Pandas Query Generator CLI

options:
  -h --help Show this help message and exit
  --max-groupby-columns Maximum number of columns in group by operations (default: 0)
  --max-merges Maximum number of table merges allowed (default: 2)
  --max-projection-columns Maximum number of columns to project (default: 0)
  --max-selection-conditions Maximum number of conditions in selection operations (default: 0)
  --multi-line Format queries on multiple lines (default: False)
  --num-queries num_queries The number of queries to generate
  --output-file The name of the file to write the results to (default: queries.txt)
  --schema schema Path to the relational schema JSON file
  --sorted Whether or not to sort the queries by complexity (default: False)
  --verbose Print extra generation information and statistics (default: False)
```

The required parameters, as shown, are `num-queries` and `schema`. The
`num-queries` parameter simply instructs the program to generate that many
queries.

The `schema` parameter is a pointer to a JSON file path that describes
meta-information about the data we're generating queries for.

A sample schema looks like this:

```json
{
  "entities": {
    "customer": {
      "primary_key": "id",
      "properties": {
        "id": {
          "type": "int",
          "min": 1,
          "max": 1000
        },
        "name": {
          "type": "string",
          "starting_character": ["A", "B", "C"]
        },
        "status": {
          "type": "enum",
          "values": ["active", "inactive"]
        }
      },
      "foreign_keys": {}
    },
    "order": {
      "primary_key": "order_id",
      "properties": {
        "order_id": {
          "type": "int",
          "min": 1,
          "max": 5000
        },
        "customer_id": {
          "type": "int",
          "min": 1,
          "max": 1000
        },
        "amount": {
          "type": "float",
          "min": 10.0,
          "max": 1000.0
        },
        "status": {
          "type": "enum",
          "values": ["pending", "completed", "cancelled"]
        }
      },
      "foreign_keys": {
        "customer_id": ["id", "customer"]
      }
    }
  }
}
```

This file can be found in `examples/customer/schema.json`, generate a few
queries from this schema with `pqg --num-queries 100 --schema examples/customer/schema.json --verbose`.

### Prior Art

This version of the Pandas Query Generator is based off of the thorough research
work of previous students of
[COMP 400](https://www.mcgill.ca/study/2023-2024/courses/comp-400) at
[McGill University](https://www.mcgill.ca/), namely Ege Satir, Hongxin Huo and
Dailun Li.
