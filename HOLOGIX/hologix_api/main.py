from fastapi import FastAPI
from hologix_api.routes import system, chat
app=FastAPI(title="HOLOGIX API")
app.include_router(system.router)
app.include_router(chat.router)
