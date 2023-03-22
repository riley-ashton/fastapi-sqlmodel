from typing import TypeVar, Type, Callable

import sqlmodel
from sqlmodel import SQLModel

from .auth import get_current_user, AccessParams

T = TypeVar("T", bound=SQLModel)

Filter = Callable[[], bool] | None
"""
A filtering function.
None means no filters; like f(x)=True.
"""


async def create(obj: T, params: AccessParams) -> T:
    """
    Persist a new object of type T in the database.
    Returns the persisted object.
    User id is automatically added, based on token.
    Can raise a credentials_exception
    """
    user = await get_current_user(params)
    obj.user_id = user.id
    session = params.session
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def select_all(of_type: Type[T], params: AccessParams) -> list[T]:
    user = await get_current_user(params)
    result = await params.session.execute(sqlmodel.select(of_type).where(of_type.user_id == user.id))
    items = result.scalars().all()
    return items


async def select_one(of_type: Type[T], where: Filter, params: AccessParams) -> T | None:
    """
    Selects zero or one item of type T from the database.
    Scoped to the given user and the filtering function is applied.
    """
    user = await get_current_user(params)
    result = await params.session.execute(sqlmodel.select(of_type).where(of_type.user_id == user.id).where(where))
    item = result.scalars().one_or_none()
    return item
