from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(min_length=1)
    email: str
    age: int = Field(ge=0, le=120)

class UserCreate(BaseModel): 
    name: str = Field(min_length=1)
    email: str
    age: int = Field(ge=0, le=120)
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    message : str
    user : UserCreate
