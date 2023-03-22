import pytest
from httpx import AsyncClient

from .models import SongBase
from .test_wrapper import wrapper


@pytest.mark.asyncio
async def test_no_user_blocked():
    async def test(client: AsyncClient):
        response = await client.get("/users/me/")
        assert response.status_code == 401

    await wrapper(test)


@pytest.mark.asyncio
async def test_user_creation():
    async def test(client: AsyncClient):
        # create user
        body = {"email": "test@test.com", "password": "secretive2000"}
        response = await client.post("/users", params=body)
        assert response.status_code == 200

    await wrapper(test)


@pytest.mark.asyncio
async def test_user_me():
    async def test(client: AsyncClient):
        response = await client.get("/users/me/")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "jane@z.co"
        assert "password" not in data
        assert "hashed_password" not in data

    await wrapper(test, user_email="jane@z.co")


@pytest.mark.asyncio
async def test_songs():
    async def test(client: AsyncClient):
        response = await client.get("/songs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        song = data[0]
        assert song["name"] == "Big Boss Rabbit"

    await wrapper(test, user_email="jane@z.co")


@pytest.mark.asyncio
async def test_create_song():
    async def test(client: AsyncClient):
        json = {"name": "Aberdeen", "artist": "Cage the Elephant", "year": 2011}
        response = await client.post("/songs", json=json)
        assert response.status_code == 200
        assert SongBase(**response.json()) == SongBase(**json)

    await wrapper(test, user_email="jane@z.co")
