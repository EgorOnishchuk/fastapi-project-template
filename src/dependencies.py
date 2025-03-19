from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from asyncpg import Connection
from fastapi import Depends, FastAPI

from src.db.db_manager import AsyncpgManager
from src.settings import (
    APISettings,
    DocsSettings,
    CORSSettings,
    CompressionSettings,
    DBSettings,
    TrustedHostsSettings,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with get_asyncpg_manager():
        yield


@lru_cache
def get_api_settings() -> APISettings:
    return APISettings()  # type: ignore


@lru_cache
def get_db_settings() -> DBSettings:
    return DBSettings()  # type: ignore


@lru_cache
def get_trusted_hosts_settings() -> TrustedHostsSettings:
    return TrustedHostsSettings()


@lru_cache
def get_cors_settings() -> CORSSettings:
    return CORSSettings()


@lru_cache
def get_compression_settings() -> CompressionSettings:
    return CompressionSettings()


@lru_cache
def get_docs_settings() -> DocsSettings:
    return DocsSettings()  # type: ignore


@lru_cache
def get_asyncpg_manager() -> AsyncpgManager:
    return AsyncpgManager(settings=get_db_settings())


AsyncpgManagerDep = Annotated[AsyncpgManager, Depends(get_asyncpg_manager)]


async def get_conn(db_manager: AsyncpgManagerDep) -> Connection:
    async with db_manager.get_conn() as conn:
        yield conn


ConnDep = Annotated[Connection, Depends(get_conn)]
