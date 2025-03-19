from dataclasses import dataclass
from typing import Any

from httpx import AsyncClient, HTTPStatusError, RequestError

from src.dependencies import get_api_settings
from src.persons.errors import ExternalAPIError
from src.schemas import Schema, from_dict


@dataclass(kw_only=True, slots=True, frozen=True)
class HTTPClient:
    url: str
    schema: type[Schema]

    session: AsyncClient = AsyncClient()
    timeout: float = get_api_settings().timeout

    @from_dict()
    async def request(self, method: str, **kwargs) -> Any:
        try:
            response = await self.session.request(
                method, self.url, timeout=self.timeout, **kwargs
            )
        except RequestError:
            raise ExternalAPIError

        try:
            response.raise_for_status()
        except HTTPStatusError:
            raise ExternalAPIError

        return response.json()
