import random
import string
import typing as t
from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class PropertyInt:
  """Represents an integer property with a defined range."""

  min: int
  max: int
  type: str = 'int'


@dataclass
class PropertyFloat:
  """Represents a float property with a defined range."""

  min: float
  max: float
  type: str = 'float'


@dataclass
class PropertyEnum:
  """Represents an enumeration property with a list of possible values."""

  values: t.List[str]
  type: str = 'enum'


@dataclass
class PropertyString:
  """Represents a string property with specified starting characters."""

  starting_character: t.List[str]
  type: str = 'string'


@dataclass
class PropertyDate:
  """Represents a date property with a defined range."""

  min: date
  max: date
  type: str = 'date'


Property = t.Union[PropertyInt, PropertyFloat, PropertyEnum, PropertyString, PropertyDate]


@dataclass
class Entity:
  """
  Represents entity information parsed from schema files.

  This class is used to generate well-formed and meaningful queries based on
  entity information and a high-level structure describing how queries should
  generally look (see `QueryStructure`).

  Attributes:
    primary_key (str | t.List[str] | None): The primary key(s) of the entity.
    properties (t.Dict[str, Property]): A dictionary of property names to their definitions.
    foreign_keys (t.Dict[str, t.List[str]]): A dictionary of foreign key relationships.
  """

  primary_key: str | t.List[str] | None
  properties: t.Dict[str, Property]
  foreign_keys: t.Dict[str, t.List[str]]

  @staticmethod
  def from_configuration(config: t.Dict) -> 'Entity':
    """
    Create an Entity instance from a configuration dictionary.

    Args:
      config (t.Dict): A dictionary containing entity configuration.

    Returns:
      Entity: An instance of the Entity class.

    Raises:
      ValueError: If an unknown property type is encountered.
    """
    properties = {}

    for name, data in config.get('properties', {}).items():
      prop_type = data['type']

      if prop_type == 'int':
        properties[name] = PropertyInt(min=data['min'], max=data['max'])
      elif prop_type == 'float':
        properties[name] = PropertyFloat(min=data['min'], max=data['max'])
      elif prop_type == 'enum':
        properties[name] = PropertyEnum(values=data['values'])
      elif prop_type == 'string':
        properties[name] = PropertyString(starting_character=data['starting_character'])
      elif prop_type == 'date':
        properties[name] = PropertyDate(
          min=date.fromisoformat(data['min']), max=date.fromisoformat(data['max'])
        )
      else:
        raise ValueError(f'Unknown property type: {prop_type}')

    return Entity(
      primary_key=config.get('primary_key', None),
      properties=properties,
      foreign_keys=config.get('foreign_keys', {}),
    )

  @property
  def has_unique_primary_key(self) -> bool:
    """Check if the entity has a single, unique primary key."""
    return isinstance(self.primary_key, str)

  @property
  def data_ranges(self) -> t.Dict[str, t.Tuple[int, int] | t.List[str]]:
    """
    Get the data ranges for all properties of the entity.

    Returns:
      A dictionary mapping property names to their respective ranges or possible values.
    """
    ranges = {}

    for name, property in self.properties.items():
      match property:
        case PropertyInt(min, max) | PropertyFloat(min, max):
          ranges[name] = (min, max)
        case PropertyString(starting_character):
          ranges[name] = (starting_character,)
        case PropertyEnum(values):
          ranges[name] = values
        case PropertyDate(min, max):
          ranges[name] = (min.isoformat(), max.isoformat())

    return ranges

  def generate_dataframe(self, num_rows=200) -> pd.DataFrame:
    """
    Generate a Pandas dataframe using this entity's information.

    Args:
      num_rows (int): The number of rows to generate. Default is 200.

    Returns:
      pd.DataFrame: A dataframe populated with randomly generated data based on the entity's properties.

    Note:
      If the entity has a unique primary key of type int, the number of rows may be limited
      to the range of possible values for that key.
    """
    rows = []

    if self.has_unique_primary_key:
      assert isinstance(self.primary_key, str)

      primary_key_property = self.properties[self.primary_key]

      if isinstance(primary_key_property, PropertyInt):
        constraint = primary_key_property.max - primary_key_property.min + 1
        num_rows = constraint if constraint < num_rows else num_rows

    for i in range(num_rows):
      row = {}

      for name, property in self.properties.items():
        match property:
          case PropertyInt(min, max):
            if (
              self.has_unique_primary_key
              and name == self.primary_key
              and num_rows == (max - min + 1)
            ):
              row[name] = i + min
            else:
              row[name] = random.randint(min, max)
          case PropertyFloat(min, max):
            row[name] = round(random.uniform(min, max), 2)
          case PropertyString(starting_character):
            starting_char = random.choice(starting_character)
            random_string = ''.join(random.choices(string.ascii_letters, k=9))
            row[name] = starting_char + random_string
          case PropertyEnum(values):
            row[name] = random.choice(values)
          case PropertyDate(min, max):
            row[name] = pd.to_datetime(
              random.choice(pd.date_range(pd.to_datetime(min), pd.to_datetime(max)))
            ).strftime('%Y-%m-%d')

      rows.append(row)

    return pd.DataFrame(rows)
