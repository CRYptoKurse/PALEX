from __future__ import annotations
from typing import Dict, List, Optional

class Type:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Type) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def is_assignable_from(self, other: 'Type') -> bool:
        if self == other:
            return True
        if self.name == 'float' and other.name == 'int':
            return True
        return False

    def is_numeric(self) -> bool:
        return self.name in {'int', 'float'}

    def is_boolean(self) -> bool:
        return self.name == 'bool'

    def is_void(self) -> bool:
        return self.name == 'void'

    def is_string(self) -> bool:
        return self.name == 'string'

    def __str__(self) -> str:
        return self.name

class PrimitiveType(Type):
    pass

class StructType(Type):
    def __init__(self, name: str, fields: Dict[str, Type]):
        super().__init__(name)
        self.fields = fields

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StructType) and self.name == other.name and self.fields == other.fields

class FunctionType(Type):
    def __init__(self, param_types: List[Type], return_type: Type):
        super().__init__('function')
        self.param_types = param_types
        self.return_type = return_type

    def __str__(self) -> str:
        params = ', '.join(str(p) for p in self.param_types)
        return f'({params}) -> {self.return_type}'

class TypeSystem:
    INT = PrimitiveType('int')
    FLOAT = PrimitiveType('float')
    BOOL = PrimitiveType('bool')
    VOID = PrimitiveType('void')
    STRING = PrimitiveType('string')

    _primitives: Dict[str, PrimitiveType] = {
        'int': INT,
        'float': FLOAT,
        'bool': BOOL,
        'void': VOID,
        'string': STRING,
    }

    @classmethod
    def resolve(cls, name: str) -> Optional[Type]:
        return cls._primitives.get(name)

    @classmethod
    def is_valid_type_name(cls, name: str) -> bool:
        return name in cls._primitives

    @classmethod
    def numeric_result_type(cls, left: Type, right: Type) -> Optional[Type]:
        if left.is_numeric() and right.is_numeric():
            return cls.FLOAT if left.name == 'float' or right.name == 'float' else cls.INT
        return None
