from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from attono_backend_core.logging.config import setup_logging
from attono_backend_core.config import AttonoBackendSettings

# Initialize shared configuration
settings = AttonoBackendSettings()

# Setup standardized logging
setup_logging(settings)

app = FastAPI(title="PRODUCT_NAME API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

