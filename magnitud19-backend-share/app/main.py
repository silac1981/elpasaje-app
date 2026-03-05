from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(title="Magnitud 19 API")

@app.get("/")
def root():
    return {"message": "Magnitud 19 API - Operativo"}

app.include_router(api_router, prefix="/api/v1")
