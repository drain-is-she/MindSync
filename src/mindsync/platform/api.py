from contextlib import asynccontextmanager
from fastapi import FastAPI
from mindsync.config import Settings
from mindsync.storage.migrations import migrate
from mindsync.storage.repository import Repository
from mindsync.simulator.seed import seed
from .context_service import SQLiteContextProvider
from .routes import router

def create_app(settings=None, agent=None):
    settings = settings or Settings.from_env()
    if agent is None:
        if settings.agent == "mock":
            from .mock_agent import run_agent
        elif settings.agent == "real":
            from mindsync.ai.agent import run_agent
        else:
            raise ValueError("MINDSYNC_AGENT must be mock or real")
        agent = run_agent

    @asynccontextmanager
    async def lifespan(app):
        migrate(settings.db_path)
        if settings.seed_demo:
            seed(settings.db_path)
        yield

    app = FastAPI(title="MindSync AI — simulated wellbeing prototype", lifespan=lifespan)
    app.state.settings = settings
    app.state.repository = Repository(settings.db_path)
    app.state.context = SQLiteContextProvider(app.state.repository, settings.stale_after_minutes)
    app.state.agent = agent
    app.include_router(router)
    return app

app = create_app()
