from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from .auth import User, create_access_token, authenticate_user, \
    get_current_user, AccessParams
from .auth import create_user as auth_create_user
from .crud import create, select_all
from .db import init_db, get_session
from .models import Song, SongBase, Token, UserBase

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.on_event("startup")
async def on_startup():
    await init_db()


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_access(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)
) -> AccessParams:
    return AccessParams(credentials_exception, token, session)


@app.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session)
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password, session)

    if not user:
        raise credentials_exception

    return create_access_token(user)


@app.post("/users", response_model=Token)
async def create_user(
        email: str,
        password: str,
        session: AsyncSession = Depends(get_session)
) -> Token:
    user = await auth_create_user(email, password, session)
    return create_access_token(user)


@app.get("/users/me/", response_model=UserBase)
async def read_users_me(access: AccessParams = Depends(get_access)) -> UserBase:
    current_user: User = await get_current_user(access)
    return UserBase(**current_user.dict())


@app.get("/songs", response_model=list[Song])
async def get_songs(access: AccessParams = Depends(get_access)) -> list[Song]:
    return await select_all(Song, access)


@app.post("/songs")
async def add_song(
        song: SongBase,
        access: AccessParams = Depends(get_access)
) -> Song:
    song = Song(**song.dict())
    song = await create(song, access)
    return song
