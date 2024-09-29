## Pandas Query Generator

**Pandas Query Generator (pqg)** is a tool designed to help users generate synthetic
[pandas](https://pandas.pydata.org/) queries for training machine learning models
that estimate query execution costs or predict cardinality.

### Usage

```present uv run src --help
usage: src [-h] --schema SCHEMA --params PARAMS
           [--export-directory EXPORT_DIRECTORY] [--verbose VERBOSE]

Pandas Query Generator CLI

options:
  -h, --help            show this help message and exit
  --schema SCHEMA       Path to the relational schema JSON file
  --params PARAMS       Path to the user-defined parameters JSON file
  --export-directory EXPORT_DIRECTORY
                        Path to export results to
  --verbose VERBOSE     Whether or not to print extra generation information
```
