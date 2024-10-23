## Pandas Query Generator 🐼

**Pandas Query Generator (pqg)** is a tool designed to help users generate synthetic
[pandas](https://pandas.pydata.org/) queries for training machine learning models
that estimate query execution costs or predict cardinality.

### Usage

Below is the standard output of `pqg --help`, which elaborates on the various
command-line arguments the tool accepts:

```present uv run pqg --help
usage: pqg [-h] [--multi-line] --num-queries NUM_QUERIES
           [--output-file OUTPUT_FILE] --query-structure QUERY_STRUCTURE
           --schema SCHEMA [--verbose]

Pandas Query Generator CLI

options:
  -h, --help            show this help message and exit
  --multi-line          Format queries on multiple lines
  --num-queries NUM_QUERIES
                        The number of queries to generate
  --output-file OUTPUT_FILE
                        The name of the file to write the results to
  --query-structure QUERY_STRUCTURE
                        Path to the user-defined query structure JSON file
  --schema SCHEMA       Path to the relational schema JSON file
  --verbose             Print extra generation information
```

### Prior Art

This version of the Pandas Query Generator is based off of the thorough research
work of previous students of [COMP 400](https://www.mcgill.ca/study/2023-2024/courses/comp-400) at [McGill University](https://www.mcgill.ca/), namely Ege Satir, Hongxin Huo and Dailun Li.
