from pydantic import BaseModel, Field


class UserCreate(BaseModel): 
    name: str = Field(min_length=1)
    email: str
    age: int = Field(ge=0, le=120)
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    name: str
    email: str
    age: int

class UserCreateResponse(BaseModel):
    message: str
    user: UserResponse

class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)