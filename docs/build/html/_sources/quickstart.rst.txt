.. _quickstart:

Quickstart Guide
===============

This guide will help you get started with using pandas-query-generator (pqg) for generating synthetic pandas DataFrame queries.

Installation
-----------

Install using pip:

.. code-block:: bash

    pip install pqg

Basic Usage
----------

Generate Queries via CLI
~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to generate queries is using the command-line interface:

.. code-block:: bash

    # Generate 100 queries using example schema
    pqg --num-queries 100 --schema examples/customer/schema.json --verbose

    # Save queries to a file
    pqg --num-queries 100 --schema examples/customer/schema.json --output-file queries.txt

    # Generate multi-line queries
    pqg --num-queries 100 --schema examples/customer/schema.json --multi-line

Generate Queries in Python
~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a simple example of generating queries programmatically:

.. code-block:: python

    from pqg import Generator, Schema, QueryStructure

    # Load schema definition
    schema = Schema.from_file('examples/customer/schema.json')

    # Configure query generation parameters
    structure = QueryStructure(
      max_merges=2,                       # Max number of table joins
      max_selection_conditions=3,         # Max WHERE conditions
      max_projection_columns=4,           # Max columns in SELECT
      selection_probability=0.7,          # 70% chance of WHERE clause
      projection_probability=0.8,         # 80% chance of column projection
      groupby_aggregation_probability=0.3 # 30% chance of GROUP BY
    )

    # Create generator
    generator = Generator(schema, structure)

    # Generate pool of queries
    query_pool = generator.generate(num_queries=100)

    # Print queries
    for query in query_pool:
      print(query)

Schema Definition
---------------

Schemas are defined in JSON format with entity (table) definitions:

.. code-block:: json

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
        }
      }
    }

Property Types
~~~~~~~~~~~~~

The following property types are supported:

- ``int``: Integer values with min/max range
- ``float``: Floating point values with min/max range
- ``string``: Text with configurable starting characters
- ``enum``: Fixed set of possible string values
- ``date``: Dates within a min/max range

Advanced Usage
-------------

Filtering Queries
~~~~~~~~~~~~~~~

Filter queries based on their execution results:

.. code-block:: python

    from pqg import QueryFilter

    # Keep only queries that return data
    query_pool.filter(QueryFilter.NON_EMPTY)

    # Keep only queries that failed
    query_pool.filter(QueryFilter.HAS_ERROR)

Query Statistics
~~~~~~~~~~~~~~

Get statistics about generated queries:

.. code-block:: python

    stats = query_pool.statistics()
    print(stats)  # Shows operation frequencies, complexity metrics

CLI Options
~~~~~~~~~~

Common command-line options:

.. code-block:: bash

    --ensure-non-empty        # Only generate queries returning data
    --filter non-empty|empty  # Filter queries by result type
    --multi-line              # Format queries across multiple lines
    --sort                    # Sort queries by complexity
    --verbose                 # Print detailed information

Next Steps
---------

- Check out the :ref:`api_reference` for detailed documentation
- See example schemas in the ``examples/`` directory
- Read the technical paper in ``docs/paper.pdf``
