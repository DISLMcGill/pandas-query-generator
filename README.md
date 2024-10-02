## Pandas Query Generator 🐼

**Pandas Query Generator (pqg)** is a tool designed to help users generate synthetic
[pandas](https://pandas.pydata.org/) queries for training machine learning models
that estimate query execution costs or predict cardinality.

### Usage

Below is the standard output of `pqg --help`, which elaborates on the various
command-line arguments the tool accepts:

```present uv run pqg --help
usage: pqg [-h] --schema SCHEMA --params PARAMS
           [--output-directory OUTPUT_DIRECTORY] [--verbose VERBOSE]

Pandas Query Generator CLI

options:
  -h, --help            show this help message and exit
  --schema SCHEMA       Path to the relational schema JSON file
  --params PARAMS       Path to the user-defined parameters JSON file
  --output-directory OUTPUT_DIRECTORY
                        Directory to write results to
  --verbose VERBOSE     Whether or not to print extra generation information
```

### Prior Art

This version of the Pandas Query Generator is based off of the thorough research
work of previous students of [COMP 400](https://www.mcgill.ca/study/2023-2024/courses/comp-400) at [McGill University](https://www.mcgill.ca/), namely Ege Satir, Hongxin Huo and Dailun Li.
