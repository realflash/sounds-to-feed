import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

from src.backend.api import audio, feed
from src.backend.core.config_manager import ConfigManager
from src.backend.core.poller import Poller
from src.backend.db.state import StateManager

# Setup standardized JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    json_ensure_ascii=False
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.DEBUG)

async def polling_task():
    config_manager = ConfigManager()
    state_manager = StateManager()
    poller = Poller(config_manager, state_manager)
    
    while True:
        try:
            logger.info("Starting polling cycle")
            await poller.poll_all()
        except Exception as e:
            logger.error(f"Error in polling cycle: {e}")
            
        # Sleep for 1 hour
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(polling_task())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="sounds-to-feed API", lifespan=lifespan)

app.include_router(feed.router)
app.include_router(audio.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)  # nosec B104
