import random
from functools import partial
from typing import Callable, Awaitable, NamedTuple

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .auth import create_user, create_access_token
from .main import app, get_session
from .models import User, Song


class _TestDb(NamedTuple):
    """
    Used for testing. One for each test case.
    Contains the sqlite in memory database, and a dictionary of users.
    """
    engine: AsyncEngine
    users: dict[str, User]


test_dbs: dict[int, _TestDb] = dict()
"""
Sqlite in memory engines and user fixtures, one for each test wrapper.
"""


async def _create_engine() -> int:
    """
    Create an engine for the
    """
    db_id = random.randint(0, 2 ** 32)
    engine = create_async_engine(f"sqlite+aiosqlite:///", echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        users = await _fill_db(session)

    test_dbs[db_id] = _TestDb(engine=engine, users=users)

    return db_id


user_pw = {
    'john@a.com': 'correct horse staple battery',
    'jane@z.co': 'password1',
}
"""
A dictionary of users and passwords.
A fixture that fills the databases.
"""


async def _fill_db(session: AsyncSession) -> dict[str, User]:
    """
    Add fixtures to the db.
    """
    users = dict()

    # Create users
    for email in user_pw:
        user = await create_user(email, user_pw[email], session)
        users[email] = user

    # Get the created users
    john = users["john@a.com"]
    jane = users["jane@z.co"]

    # Create objects in the database
    song1 = Song(name="Where Is My Mind?", artist="Pixies", year=1988, user_id=john.id)
    song2 = Song(name="Big Boss Rabbit", artist="Freddie Gibbs", user_id=jane.id)
    session.add(song1)
    session.add(song2)
    await session.commit()
    return users


async def _session_fixture(db_id: int) -> AsyncSession:
    """
    Create an async sqlite db session with the given `id` as the db/file name.

    See `_wrapper` for using this with FastApi dependency override
    """
    async_session = sessionmaker(
        test_dbs[db_id].engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


Test = Callable[[AsyncClient], Awaitable[None]]
"""
A test async function that takes a AsyncClient and makes assertions.
Called in a wrapper.
"""


async def wrapper(tests: Test, user_email: str | None = None):
    """
    Wrapper around a test that takes a callable function
    with an argument for an async client.

    Prior to calling tests it creates the sqlite db and async client,
    fills the db with test data and overrides the get_session
    function used with FastAPI.

    Takes a user's email, which will put a token for the user in the
    header of the AsyncClient. Leaving this empty will leave the header empty.
    """
    db_id = await _create_engine()
    f = partial(_session_fixture, db_id=db_id)

    app.dependency_overrides[get_session] = f

    async with AsyncClient(app=app, base_url="http://test") as client:
        if user_email is not None and user_email in user_pw:
            user = test_dbs[db_id].users[user_email]
            token = create_access_token(user)["access_token"]
            client.headers = {"Authorization": f"Bearer {token}"}

        await tests(client)

    app.dependency_overrides.clear()
