import json
import typing as t
from collections.abc import Mapping
from dataclasses import dataclass, field

from .entity import Entity


@dataclass
class Schema(Mapping):
  """
  A dictionary-like class representing a database schema containing multiple entities.

  The Schema class provides dictionary-style access to Entity objects, allowing for
  both iteration over entities and direct access to specific entities by name.

  Attributes:
    entities (t.Set[Entity]): Set of Entity objects in the schema.
    _entity_map (t.Dict[str, Entity]): Internal mapping of entity names to Entity objects.
  """

  entities: t.Set[Entity] = field(default_factory=set)
  _entity_map: t.Dict[str, Entity] = field(init=False)

  def __post_init__(self):
    """Initialize the internal entity mapping after entity set is created."""
    self._entity_map = {entity.name: entity for entity in self.entities}

  def __getitem__(self, key: str) -> Entity:
    """
    Get an entity by name using dictionary-style access.

    Args:
      key (str): The name of the entity to retrieve.

    Returns:
      Entity: The requested entity.

    Raises:
      KeyError: If no entity exists with the given name.
    """
    return self._entity_map[key]

  def __iter__(self) -> t.Iterator[Entity]:
    """
    Iterate over all entities in the schema.

    Returns:
      Iterator[Entity]: Iterator yielding Entity objects.
    """
    return iter(self.entities)

  def __len__(self) -> int:
    """
    Get the number of entities in the schema.

    Returns:
      int: Total number of entities.
    """
    return len(self.entities)

  @staticmethod
  def from_dict(data: dict) -> 'Schema':
    """
    Create a Schema instance from a dictionary.

    Similar to from_file but accepts a dictionary directly instead of reading
    from a file. This is useful for creating schemas programmatically or when
    the schema definition is already in memory.

    Args:
      data (dict):
        Dictionary containing the schema configuration.
        Expected to have an 'entities' key mapping to entity configs.

    Returns:
      Schema: A new Schema instance containing the entities defined in the dictionary.

    Raises:
      ValueError: If the dictionary structure is invalid.

    Example:
      schema_dict = {
          "entities": {
              "customer": {
                  "primary_key": "id",
                  "properties": {...},
                  "foreign_keys": {...}
              }
          }
      }
      schema = Schema.from_dict(schema_dict)
    """
    if 'entities' not in data:
      return Schema(entities=set())

    if not isinstance(data['entities'], dict):
      raise ValueError("'entities' must be a dictionary")

    try:
      return Schema(
        set(
          Entity.from_configuration(name, configuration)
          for name, configuration in data['entities'].items()
        )
      )
    except Exception as e:
      raise ValueError(f'Invalid schema configuration: {str(e)}') from e

  @staticmethod
  def from_file(path: str) -> 'Schema':
    """
    Create a Schema instance by loading entity configurations from a JSON file.

    This method reads a JSON file containing entity configurations and creates
    a Schema object with Entity instances for each configured entity.

    Args:
      path (str): The file path to the JSON configuration file.

    Returns:
      Schema: A new Schema instance containing the entities defined in the file.

    Raises:
      json.JSONDecodeError: If the file contains invalid JSON.
      FileNotFoundError: If the specified file does not exist.
      PermissionError: If the file cannot be read due to permission issues.

    Note:
      If the 'entities' key is not present in the JSON file, an empty Schema
      will be returned.

    Example:
      schema = Schema.from_file('path/to/schema_config.json')
    """

    try:
      with open(path, 'r') as file:
        content = json.load(file)
    except json.JSONDecodeError as e:
      raise ValueError(f'Invalid JSON in file {path}: {str(e)}') from e
    except (FileNotFoundError, PermissionError) as e:
      raise IOError(f'Error reading file {path}: {str(e)}') from e

    if 'entities' not in content:
      return Schema(entities=set())

    entities = set(
      Entity.from_configuration(name, configuration)
      for name, configuration in content['entities'].items()
    )

    return Schema(entities)
