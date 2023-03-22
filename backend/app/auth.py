import sys
import uuid
from datetime import timedelta, datetime
from typing import TypeVar, NamedTuple

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import User

try:
    file = open('./SECRET_KEY', 'r')
    SECRET_KEY = file.read()
    file.close()
except OSError:
    file = open('/run/secrets/SECRET_KEY', 'r')
    SECRET_KEY = file.read()
    file.close()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if "pytest" in sys.modules:
    # if testing reduce the hash complexity
    pwd_context = CryptContext(
        schemes=["argon2"],
        deprecated="auto",
        argon2__rounds=1,
        argon2__memory_cost=1024
    )
else:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User | bool:
    """
    Returns false if user cannot be authenticated, or the User if they were
    successfully authenticated
    """
    user = await _select_user_by_email(email, session)

    if user and verify_password(password, user.hashed_password):
        return user
    else:
        return False


def create_access_token(user: User):
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user.id), "exp": expires}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}


ExceptionType = TypeVar('ExceptionType', bound=BaseException)


class AccessParams(NamedTuple):
    credentials_exception: ExceptionType
    token: str
    session: AsyncSession


async def get_current_user(params: AccessParams) -> User:
    try:
        payload = jwt.decode(params.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise params.credentials_exception
    except JWTError:
        raise params.credentials_exception
    user = await _select_user(user_id, params.session)

    if user is None:
        raise params.credentials_exception
    return user


async def create_user(email: str, password: str, session: AsyncSession) -> User:
    hashed_password = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_password)
    return await _create_user(user, session)


# TODO move elsewhere?
async def _create_user(user: User, session: AsyncSession) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# TODO move elsewhere?
async def _select_user(user_id: uuid.UUID | str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().one_or_none()
    return user


# TODO move elsewhere?
async def _select_user_by_email(email: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().one_or_none()
    return user
