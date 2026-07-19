from fastapi import FastAPI

app = FastAPI(
    title="LUIP API",
    version="1.0.0",
    description="Lawyered Up Intelligence Platform"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to LUIP API",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }