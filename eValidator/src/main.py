"""
The eValidator service monitors data events received from a Data Broker, checking for specific conditions within a configurable
time-frame.
If certain conditions are met, it publishes an error event as a Cloud Event.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import aiormq
import aiormq.abc
from cloudevents.conversion import to_json
from cloudevents.http import CloudEvent
from settings import (
    APP_AMQP,
    APP_EVENT_ATTRIBUTES,
    APP_LOG_LEVEL,
    APP_LOG_NAME,
    VALIDATION_WINDOW_MS,
)

logger = logging.getLogger(__name__)

# set up custom logging
logging.basicConfig(
    filename=None,
    level=APP_LOG_LEVEL,
    format=f"%(asctime)s: %(levelname)7s: [{APP_LOG_NAME}] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# store incoming tasks for processing
tasks_map = {}


async def publish_to_error_queue(messages):
    event = CloudEvent(APP_EVENT_ATTRIBUTES, messages)

    # TODO: sucks for reliability and ack
    connection = await aiormq.connect(APP_AMQP["url"])
    channel = await connection.channel()
    await channel.basic_publish(to_json(event), routing_key=APP_AMQP["routing_key"])


async def on_message(message: aiormq.abc.DeliveredMessage):
    """
    NOTE: sqlite calls are blocking, but have no performance hit here
    """
    logger.debug(f"received on_message: {message}")

    try:
        payload = json.loads(message.body)
        data = payload["data"]
        data_received = datetime.now(timezone.utc)
        data_hash = data["hash"]
        data["received"] = data_received

        # https://wiki.python.org/moin/TimeComplexity#:~:text=is%20a%20list.-,dict,-The%20Average%20Case
        # same time complexity in vs get for dict
        previous_data = tasks_map.get(data_hash)
        logger.debug("1" * 50)
        logger.debug(tasks_map)
        if previous_data:
            # inside validation window
            logger.debug("2" * 50)
            if data_received - previous_data["received"] <= VALIDATION_WINDOW_MS:
                logger.debug("3" * 50)
                if data_received["type"] + previous_data["type"] >= 10:
                    logger.debug("4" * 50)
                    # delete received information from items
                    del data["received"]
                    del previous_data["received"]
                    await publish_to_error_queue([data_received, previous_data])
            else:
                logger.debug("5" * 50)
                # overwrite previous hashes?
                tasks_map[data_hash] = data
        else:
            logger.debug("6" * 50)
            tasks_map[data_hash] = data

    except Exception as e:
        logger.debug("7" * 50)
        logger.error(f"Exception occurred: {e}")


async def set_up_queues():
    """
    TODO: make this work
    asyncio loop hangs after 1 iteration
    with no explicit Exception... probably aiormq thing
    """

    # Perform connection
    connection = await aiormq.connect(APP_AMQP["url"])

    # Creating a channel
    channel = await connection.channel()
    # Declaring queue
    declare_ok = await channel.queue_declare(APP_AMQP["error_queue_name"], durable=True)
    # declare_ok = await channel.queue_declare(APP_AMQP["queue_name"], durable=True)
    await channel.queue_bind(APP_AMQP["queue_name"], APP_AMQP["exchange_name"])
    await channel.basic_qos(prefetch_count=1)

    # Start listening the queue
    await channel.basic_consume(APP_AMQP["queue_name"], on_message, no_ack=False)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_up_queues())

    # we enter a never-ending loop that waits for data and runs
    # callbacks whenever necessary.
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt. Bye!")

"""
{
    "data": {
        "hash": "661f8009fa8e56a9d0e94a0a644397d7",
        "status": "complete",
        "type": 11,
    },
    "datacontenttype": "application/json",
    "id": "a8d148a8-e44b-47f2-a07e-65a355d98437",
    "source": "ereceiver",
    "specversion": "1.0",
    "subject": "DATA",
    "time": "2024-10-01T12:07:03.861973+00:00",
    "type": "com.evertest.event",
}
"""
