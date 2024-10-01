import aiormq
from cloudevents.conversion import to_json
from cloudevents.http import CloudEvent
from fastapi import APIRouter
from settings import APP_AMQP, APP_EVENT_ATTRIBUTES

from ..models.task import TaskItem

router = APIRouter()


@router.post("/")
async def data(item: TaskItem):
    event = CloudEvent(APP_EVENT_ATTRIBUTES, item.model_dump())

    # TODO: sucks for reliability and ack
    connection = await aiormq.connect(APP_AMQP["url"])
    channel = await connection.channel()
    await channel.basic_publish(
        to_json(event),
        routing_key=APP_AMQP["routing_key"],
        exchange=APP_AMQP["exchange_name"],
    )

    return to_json(event)
