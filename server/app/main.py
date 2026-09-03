import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from server.app.database import init_db
from server.app.routes.api import router as api_router
from server.app.routes.views import router as views_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("parts_database")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context initializing SQLite WAL database and seed data on startup."""
    logger.info("Initializing Parts-Database Web Catalog Server...")
    await init_db()
    yield
    logger.info("Parts-Database Web Catalog Server shutting down cleanly.")


app = FastAPI(
    title="Parts-Database Web Catalog & Inventory Microservice",
    description="Physical workshop inventory platform linking 3D-printed Gridfinity modular bins to a web catalog via QR codes.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(api_router)
app.include_router(views_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app.main:app", host="0.0.0.0", port=8090, reload=True)
