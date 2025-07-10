from uuid import uuid4
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class UserORM(Base):
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(default="user")
    current_token: Mapped[str] = mapped_column(nullable=True)

class User(BaseModel):
    id: str
    username: str
    password: str
    full_name: str
    enabled: bool = True
    role: str = "user"
    current_token: str | None = None