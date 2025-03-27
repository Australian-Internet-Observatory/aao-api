
from enum import Enum
from typing import List, Union, Optional
from pydantic import BaseModel

class ProjectMemberRole(Enum):
    ADMIN = 'admin'
    VIEWER = 'viewer'
    EDITOR = 'editor'
    
    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value
    
    @staticmethod
    def parse(role: str):
        return ProjectMemberRole[role.upper()]
    
    @staticmethod
    def equals(role: Union[str, 'ProjectMemberRole'], other: Union[str, 'ProjectMemberRole']):
        # Convert to enum if string
        if isinstance(role, str):
            role = ProjectMemberRole.parse(role)
        if isinstance(other, str):
            other = ProjectMemberRole.parse(other)
        return role == other

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