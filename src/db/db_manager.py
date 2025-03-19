from abc import ABC, abstractmethod
from asyncio import CancelledError
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import Any

from asyncpg import Pool, create_pool
from asyncpg.pool import PoolConnectionProxy

from src.data_access_layer import AsyncpgDAL
from src.errors import DBConnError
from src.settings import DBSettings


@dataclass(kw_only=True)
class DBManager(ABC):
    settings: DBSettings
    clear: bool = False

    def __post_init__(self) -> None:
        self.timeout = self.settings.timeout

    @abstractmethod
    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[Any, None]:
        pass

    @abstractmethod
    async def __aenter__(self) -> None:
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass


class AsyncpgManager(DBManager):
    pool: Pool | None = None

    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[PoolConnectionProxy, None]:
        try:
            async with self.pool.acquire(timeout=self.timeout) as conn:
                async with conn.transaction():
                    yield conn
        except CancelledError:
            raise DBConnError

    async def __aenter__(self):
        self.pool = await create_pool(
            f"postgresql://{self.settings.user}:{self.settings.password}@{self.settings.host}"
            f"/{self.settings.db_name}",
            **self.settings.model_dump(
                by_alias=True,
                exclude={"dsn", "timeout", "user", "password", "host", "db_name"},
            ),
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.clear:
            async with self.get_conn() as conn:
                conn.execute(
                    f"TRUNCATE"
                    f" {', '.join(cls.schema.__name__.lower() for cls in AsyncpgDAL.__subclasses__())}"
                )
        await self.pool.close()
