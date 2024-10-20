from fastapi import FastAPI
from app.routers import post, users, auth  

app = FastAPI()

app.include_router(post.router)
app.include_router(users.router)
app.include_router(auth.router)
