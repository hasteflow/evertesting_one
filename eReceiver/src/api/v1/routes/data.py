import json

import aiormq
from cloudevents.conversion import to_dict
from cloudevents.http import CloudEvent
from fastapi import APIRouter
from settings import APP_AMQP, APP_EVENT_ATTRIBUTES

from ..models.task import TaskItem

router = APIRouter()


def get_json_event(event):
    return json.dumps(to_dict(event))


@router.post("/")
async def data(item: TaskItem):
    event = CloudEvent(APP_EVENT_ATTRIBUTES, item.model_dump())
    json_payload = get_json_event(event)

    # TODO: sucks for reliability and ack
    connection = await aiormq.connect(APP_AMQP["url"])
    channel = await connection.channel()

    await channel.basic_publish(
        json_payload.encode("utf-8"),
        routing_key=APP_AMQP["routing_key"],
        exchange=APP_AMQP["exchange_name"],
    )

    return json_payload
