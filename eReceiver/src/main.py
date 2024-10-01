"""
The eReceiver service is an HTTP server dedicated to handling a single endpoint that accepts data via HTTP POST requests.

Its primary functions include
    - validating incoming data
    - logging errors for invalid data
    - publishing valid data as Cloud Events to a Data
"""

import asyncio
import importlib
import logging

import aiormq
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from settings import (
    APP_AMQP,
    APP_LOG_LEVEL,
    APP_LOG_NAME,
    APP_PORT,
    APP_ROUTES,
    APP_ROUTES_PACKAGE_NAME,
)

logger = logging.getLogger(__name__)

app = FastAPI()


# set up custom logging
logging.basicConfig(
    filename=None,
    level=APP_LOG_LEVEL,
    format=f"%(asctime)s: %(levelname)7s: [{APP_LOG_NAME}] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exception):
    logger.error(
        f"Input data is not valid: {await request.json()}"
    )  # , exc_info=exception) # for detailed exception
    raise HTTPException(status_code=422, detail=jsonable_encoder(exception.errors()))


async def set_up_queue():
    """
    TODO: Simple setup. Needs improvement
    """
    connection = await aiormq.connect(APP_AMQP["url"])
    # Creating a channel
    channel = await connection.channel()

    await channel.exchange_declare(
        exchange=APP_AMQP["exchange_name"], exchange_type=APP_AMQP["exchange_type"]
    )

    for queue_name in APP_AMQP["queue_names"].values():
        declare_ok = await channel.queue_declare(queue_name, durable=True)
        await channel.queue_bind(declare_ok.queue, APP_AMQP["exchange_name"])


# create queue before any routes are initialized
loop = asyncio.get_event_loop()
loop.run_until_complete(set_up_queue())


for route_name, route_prefix in APP_ROUTES.items():
    try:
        module_name = f"{APP_ROUTES_PACKAGE_NAME}.{route_name}"
        module = importlib.import_module(module_name)
        app.include_router(module.router, prefix=route_prefix)
    except ModuleNotFoundError as e:
        raise SystemError(f"Cannot import module {module_name} {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_config=None)
