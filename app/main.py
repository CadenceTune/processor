from fastapi import FastAPI
from app.router import router

app = FastAPI(title="CadenceTune Processor Service", version="1.0.0")

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "UP"}