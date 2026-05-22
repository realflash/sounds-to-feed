import logging
import os

import uvicorn
from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

# Setup standardized JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI(title="sounds-to-feed API")

# Removed CORS middleware to satisfy semgrep security scan (not needed for RSS feed)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)  # nosec B104
