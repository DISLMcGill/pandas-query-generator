from enum import Enum


class ComparisonOperator(Enum):
  EQ = '=='
  GE = '>='
  GT = '>'
  IN = 'in'
  LE = '<='
  LT = '<'
  NE = '!='
  STARTS_WITH = '.str.startswith'


class ConditionalOperator(Enum):
  AND = '&'
  OR = '|'
