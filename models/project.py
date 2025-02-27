from typing import List, Union, Optional
from dataclasses import dataclass

@dataclass
class Method:
    label: str
    value: str
    type: str
    precedence: int
    associativity: str
    inputType: Optional[str] = None

@dataclass
class Query:
    method: str
    args: List[Union['Query', str]]

@dataclass
class TeamMember:
    username: str
    role: str

@dataclass
class TextCell:
    id: str
    type: str
    content: str

@dataclass
class QueryResultConfig:
    sort: str
    groupBy: str

@dataclass
class QueryResult:
    id: str
    type: str
    config: Optional[QueryResultConfig] = None

@dataclass
class QueryCellContent:
    query: Query
    results: List[QueryResult]

@dataclass
class QueryCell:
    id: str
    type: str
    content: QueryCellContent

Cell = Union[TextCell, QueryCell]

@dataclass
class Project:
    id: str
    name: str
    description: str
    ownerId: str
    team: List[TeamMember]
    cells: List[Cell]