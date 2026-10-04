from fastapi import FastAPI

from app.database.connection import Base, engine
from app.models import user
from app.routers import users

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message" : "Welcome to my FastAPI project"
    }

app.include_router(users.router)