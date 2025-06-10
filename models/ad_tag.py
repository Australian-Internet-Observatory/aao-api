from typing import List
from pydantic import BaseModel

class AdTag(BaseModel):
    id: str
    tags: List[str]