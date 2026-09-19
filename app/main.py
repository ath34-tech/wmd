from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Personal Fitness Coach API",
    description="Backend API for the local-first fitness companion.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Personal Fitness Coach API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Mangum wrapper for AWS Lambda execution
handler = Mangum(app)
