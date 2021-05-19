import asyncio
import fastapi_plugins

from aioredis import Redis, Channel
from sse_starlette.sse import EventSourceResponse
from faker import Faker

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Depends

app = FastAPI()
faker = Faker()

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def on_startup() -> None:
    await fastapi_plugins.redis_plugin.init_app(app)
    await fastapi_plugins.redis_plugin.init()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await fastapi_plugins.redis_plugin.terminate()


@app.get("/fake-data")
async def fake_data(
    channel: str = "default", redis: Redis = Depends(fastapi_plugins.depends_redis)
):
    for i in range(10):
        post = faker.sentence(nb_words=10)
        await redis.publish(channel=channel, message=post)
        await asyncio.sleep(5)


@app.get("/sse/stream")
async def stream(
    channel: str = "default", redis: Redis = Depends(fastapi_plugins.depends_redis)
):
    return EventSourceResponse(subscribe(channel, redis))


async def subscribe(channel: str, redis: Redis):
    (channel_subscription,) = await redis.subscribe(channel=Channel(channel, False))
    while await channel_subscription.wait_message():
        yield {"event": "message", "data": await channel_subscription.get()}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
