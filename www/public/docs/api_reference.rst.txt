.. _api_reference:

API Reference
============

This reference documents the key classes and functions in pqg.

Schema Components
---------------

Schema
~~~~~~

.. autoclass:: pqg.Schema
    :members:
    :special-members: __getitem__, __iter__, __len__

Entity
~~~~~~

.. autoclass:: pqg.Entity
    :members:
    :special-members: __hash__, __eq__

Property Types
~~~~~~~~~~~~~

.. autoclass:: pqg.PropertyInt
    :members:

.. autoclass:: pqg.PropertyFloat
    :members:

.. autoclass:: pqg.PropertyEnum
    :members:

.. autoclass:: pqg.PropertyString
    :members:

.. autoclass:: pqg.PropertyDate
    :members:

Query Generation
--------------

Generator
~~~~~~~~~

.. autoclass:: pqg.Generator
    :members:

GenerateOptions
~~~~~~~~~~~~~

.. autoclass:: pqg.GenerateOptions
    :members:

QueryStructure
~~~~~~~~~~~~~

.. autoclass:: pqg.QueryStructure
    :members:

Query Components
--------------

Query
~~~~~

.. autoclass:: pqg.Query
    :members:
    :special-members: __str__, __hash__, __eq__, __lt__

Operations
~~~~~~~~~

.. autoclass:: pqg.Operation
    :members:

.. autoclass:: pqg.Selection
    :members:

.. autoclass:: pqg.Projection
    :members:

.. autoclass:: pqg.GroupByAggregation
    :members:

.. autoclass:: pqg.Merge
    :members:

Query Management
--------------

QueryPool
~~~~~~~~

.. autoclass:: pqg.QueryPool
    :members:
    :special-members: __len__, __iter__

QueryFilter
~~~~~~~~~~

.. autoclass:: pqg.QueryFilter
    :members:

Statistics
~~~~~~~~~

.. autoclass:: pqg.query_pool.ExecutionStatistics
    :members:

.. autoclass:: pqg.query_pool.QueryStatistics
    :members:

Command Line Interface
--------------------

The package provides a command-line interface through the ``pqg`` command.
See the :ref:`quickstart` guide for common usage examples.

Arguments
~~~~~~~~

.. autoclass:: pqg.Arguments
    :members:

The following command-line arguments are available:

--disable-multi-processing
    Generate and execute queries sequentially

--ensure-non-empty
    Only generate queries that return data

--filter {non-empty,empty,has-error,without-error}
    Filter queries by execution results

--groupby-aggregation-probability FLOAT
    Probability of including GROUP BY operations (default: 0.5)

--max-groupby-columns INT
    Maximum columns in GROUP BY clauses (default: 5)

--max-merges INT
    Maximum number of table joins (default: 2)

--max-projection-columns INT
    Maximum columns to select (default: 5)

--max-selection-conditions INT
    Maximum WHERE conditions (default: 5)

--multi-line
    Format queries across multiple lines

--num-queries INT
    Number of queries to generate [required]

--output-file FILE
    Save queries to a file

--projection-probability FLOAT
    Probability of including projections (default: 0.5)

--schema FILE
    Schema definition file [required]

--selection-probability FLOAT
    Probability of including selections (default: 0.5)

--sort
    Sort queries by complexity

--verbose
    Print detailed information

Error Handling
-------------

The following exceptions may be raised:

ValueError
    Raised for invalid configurations or parameters

IOError
    Raised for schema file read errors

Examples
--------

See the :ref:`quickstart` guide for usage examples.
