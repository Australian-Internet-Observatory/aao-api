
from typing import List, Union, Optional
from pydantic import BaseModel

class Query(BaseModel):
    method: str
    args: List[Union['Query', str]]

class TeamMember(BaseModel):
    username: str
    role: str

class TextCell(BaseModel):
    id: str
    type: str
    content: str

class QueryResultConfig(BaseModel):
    sort: str
    groupBy: str

class QueryResult(BaseModel):
    id: str
    type: str
    config: Optional[QueryResultConfig] = None

class QueryCellContent(BaseModel):
    query: Query
    results: List[QueryResult]

class QueryCell(BaseModel):
    id: str
    type: str
    content: QueryCellContent

Cell = Union[TextCell, QueryCell]

class Project(BaseModel):
    id: str
    name: str
    description: str
    ownerId: str
    team: List[TeamMember]
    cells: List[Cell]

