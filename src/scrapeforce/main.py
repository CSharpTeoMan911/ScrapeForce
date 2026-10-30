import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from scrapeforce.Utilities.proxy_test import ProxyTest

proxy_test = ProxyTest()

global vars  # noqa: PLW0604
config = Path.joinpath(Path.cwd(), "Utilities", "config.json")
vars = {"allowed_origins": []}


if not os.path.exists(config):
    with open(config, "w") as fw:
        fw.write(json.dumps(vars, indent=4))
        fw.flush()
    print("\n[ [!!!] Configuration file created [!!!] ]\n")
else:
    with open(config, "r") as fr:
        origins = fr.read()
        vars = json.loads(origins)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.proxy_test = proxy_test
    try:
        proxy_test.test_proxies()
        yield
    finally:
        await asyncio.to_thread(proxy_test.shutdown_test)

print("[ Waiting for proxy extraction . . . ]")

app = FastAPI(lifespan=lifespan)


origins = vars["allowed_origins"]

if os.path.exists(config) and len(origins) > 0:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}
