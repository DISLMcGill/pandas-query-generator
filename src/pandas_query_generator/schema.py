import json
import typing as t
from dataclasses import dataclass

from .entity import Entity


@dataclass
class Schema:
  """
  Represents a schema containing multiple entities.

  This class is responsible for loading and storing multiple Entity objects
  from a configuration file. It provides a convenient way to access and
  manage multiple entities within a single schema.

  Attributes:
    entities (t.Dict[str, Entity]):
      A dictionary mapping entity names to their corresponding Entity objects.
  """

  entities: t.Dict[str, Entity]

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
      return Schema(entities={})

    entities = content['entities']

    return Schema(
      entities={
        name: Entity.from_configuration(configuration) for name, configuration in entities.items()
      }
    )
