## Pandas Query Generator 🐼

**Pandas Query Generator (pqg)** is a tool designed to help users generate synthetic
[pandas](https://pandas.pydata.org/) queries for training machine learning models
that estimate query execution costs or predict cardinality.

### Usage

Below is the standard output of `pqg --help`, which elaborates on the various
command-line arguments the tool accepts:

```present uv run pqg --help
usage: pqg [-h] [--max-groupby-columns MAX_GROUPBY_COLUMNS]
           [--max-merges MAX_MERGES]
           [--max-projection-columns MAX_PROJECTION_COLUMNS]
           [--max-selection-conditions MAX_SELECTION_CONDITIONS]
           [--multi-line] --num-queries NUM_QUERIES
           [--output-file OUTPUT_FILE] --schema SCHEMA [--sorted] [--verbose]

Pandas Query Generator CLI

options:
  -h, --help            show this help message and exit
  --max-groupby-columns MAX_GROUPBY_COLUMNS
                        Maximum number of columns in group by operations
                        (default: 0)
  --max-merges MAX_MERGES
                        Maximum number of table merges allowed (default: 2)
  --max-projection-columns MAX_PROJECTION_COLUMNS
                        Maximum number of columns to project (default: 0)
  --max-selection-conditions MAX_SELECTION_CONDITIONS
                        Maximum number of conditions in selection operations
                        (default: 0)
  --multi-line          Format queries on multiple lines (default: False)
  --num-queries NUM_QUERIES
                        The number of queries to generate (default: None)
  --output-file OUTPUT_FILE
                        The name of the file to write the results to (default:
                        queries.txt)
  --schema SCHEMA       Path to the relational schema JSON file (default:
                        None)
  --sorted              Whether or not to sort the queries by complexity
                        (default: False)
  --verbose             Print extra generation information and statistics
                        (default: False)
```

### Prior Art

This version of the Pandas Query Generator is based off of the thorough research
work of previous students of [COMP 400](https://www.mcgill.ca/study/2023-2024/courses/comp-400) at [McGill University](https://www.mcgill.ca/), namely Ege Satir, Hongxin Huo and Dailun Li.
