from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


NonEmptyStr = Annotated[str, Field(min_length=1)]

SchemaT = TypeVar("SchemaT", bound="Schema")


class Schema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @staticmethod
    def to_tuple(
        func: Callable[[Any, SchemaT, ...], Awaitable[Any]],
    ) -> Callable[[Any, tuple, ...], Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self: Any, schema: SchemaT, *args: Any, **kwargs: Any) -> Any:
            tuple_ = tuple(schema.model_dump().values())

            return await func(self, tuple_, *args, **kwargs)

        return wrapper


def from_res(
    transformer: Callable[[Any, type[SchemaT]], SchemaT],
) -> Callable[[Any, ...], Awaitable[Any]]:
    def decorator(
        func: Callable[[Any, ...], Awaitable[Any]],
    ) -> Callable[[Any, ...], Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            res = await func(self, *args, **kwargs)
            return transformer(res, self.schema) if res is not None else None

        return wrapper

    return decorator


def from_dict() -> Callable[
    [Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]
]:
    return from_res(lambda res, schema: schema(**dict(res)))


def from_dicts() -> Callable[
    [Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]
]:
    return from_res(lambda seq, schema: [schema(**dict(res)) for res in seq])


class Error(Schema):
    reason: Annotated[NonEmptyStr, Field(examples=["Not available"])]
    ways_to_solve: Annotated[
        list[NonEmptyStr],
        Field(
            min_length=1, examples=[["Try again", "Try later", "Contact to support"]]
        ),
    ]
