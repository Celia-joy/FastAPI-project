from fastapi import FastAPI
from app.routers import users

app = FastAPI()

@app.get("/")
def home():
    return {
        "message" : "Welcome to my FastAPI project"
    }

app.include_router(users.router)