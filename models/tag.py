from pydantic import BaseModel

class Tag(BaseModel):
    id: str
    name: str
    description: str
    hex: str