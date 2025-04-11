from pydantic import BaseModel


class Ad(BaseModel):
    observer_id: str
    ad_id: str
    timestamp: str
    attributes: dict | None