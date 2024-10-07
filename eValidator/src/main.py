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
from cloudevents.conversion import from_json, to_dict
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


connection, channel = None, None
# store incoming events for processing
events_map = {}


def get_json_event(event):
    return json.dumps(to_dict(event))


async def publish_to_error_queue(messages):
    global connection, channel

    if connection is None or channel is None:
        logger.error(f"Invalid connection or channel {connection=}, {channel=}")
        return

    event = CloudEvent(APP_EVENT_ATTRIBUTES, messages)
    json_payload = get_json_event(event)
    logger.debug(
        f"Publishing to error queue:`{APP_AMQP['routing_key']}`, event:`{json_payload}`"
    )
    await channel.basic_publish(
        json_payload.encode("utf-8"), routing_key=APP_AMQP["routing_key"]
    )


async def on_message(message: aiormq.abc.DeliveredMessage):
    global channel

    try:
        event = from_json(CloudEvent, data=message.body)
        logger.debug(f"Received event:`{event}`")

        data = event.get_data()
        data_hash = data["hash"]
        data["received"] = datetime.now(timezone.utc)

        # https://wiki.python.org/moin/TimeComplexity#:~:text=is%20a%20list.-,dict,-The%20Average%20Case
        # same time complexity in vs get for dict
        previous_data = events_map.get(data_hash)

        if previous_data:
            # overwrite previous hashes with fresh data
            events_map[data_hash] = data

            # inside validation window
            if data["received"] - previous_data["received"] <= VALIDATION_WINDOW_MS:
                if data["type"] + previous_data["type"] >= 10:
                    # avoid mutation
                    item_1 = {**previous_data}
                    item_2 = {**data}
                    # remove received timestamp from dicts
                    _, _ = item_1.pop("received", None), item_2.pop("received", None)
                    await publish_to_error_queue([item_1, item_2])
        else:
            events_map[data_hash] = data

    except KeyError as e:
        logger.error(f"KeyError occurred: {e}")
    except Exception as e:
        logger.error(f"Exception occurred: {e}, {type(e)}")
        # do not confirm the message on error
        await channel.basic_nack(message.delivery_tag)
        return

    await channel.basic_ack(message.delivery_tag)


async def set_up_queues():
    global connection, channel

    # Perform connection and create channel
    connection = await aiormq.connect(APP_AMQP["url"])
    channel = await connection.channel()

    # Bind queues and settings
    await channel.queue_bind(APP_AMQP["error_queue_name"], APP_AMQP["exchange_name"])
    await channel.queue_bind(APP_AMQP["queue_name"], APP_AMQP["exchange_name"])
    await channel.basic_qos(prefetch_count=1)

    # Start listening the queue
    await channel.basic_consume(APP_AMQP["queue_name"], on_message, no_ack=False)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
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
