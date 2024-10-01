"""
The eProcessor service is responsible for interfacing with a local database and processing data events received from a Data
Broker.
Its main functions include
    - querying and updating the database based on the data received.
"""

import asyncio
import json
import logging
import sqlite3
from sqlite3 import IntegrityError, OperationalError

import aiormq
import aiormq.abc
from settings import APP_AMQP, APP_DATABASE_NAME, APP_LOG_LEVEL, APP_LOG_NAME

logger = logging.getLogger(__name__)

# set up custom logging
logging.basicConfig(
    filename=None,
    level=APP_LOG_LEVEL,
    format=f"%(asctime)s: %(levelname)7s: [{APP_LOG_NAME}] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def upsert_item(data):
    connection = sqlite3.connect(APP_DATABASE_NAME)
    cursor = connection.cursor()

    """
    upserting because anything else feels wrong
    """
    cursor.execute(
        """
        INSERT INTO tasks (hash, status, type)
        VALUES (:hash, :status, :type)
        ON CONFLICT(hash)
        DO UPDATE SET
            status=:status,
            type=:type;
        """,
        data,
    )
    connection.commit()


async def on_message(message: aiormq.abc.DeliveredMessage):
    """
    NOTE: sqlite calls are blocking, but have no performance hit here
    """

    try:
        data = json.loads(message.body)
        upsert_item(data.get("data"))

    except (OperationalError, IntegrityError) as e:
        logger.error(f"Exception database occurred: {e}")
    except Exception as e:
        logger.error(f"Exception occurred: {e}")


async def main():
    # Perform connection
    connection = await aiormq.connect(APP_AMQP["url"])

    # Creating a channel
    channel = await connection.channel()
    await channel.basic_qos(prefetch_count=1)

    # Declaring queue
    declare_ok = await channel.queue_declare(APP_AMQP["queue_name"], durable=True)

    # Start listening the queue
    await channel.basic_consume(declare_ok.queue, on_message, no_ack=False)


def set_up_database():
    """
    Set up database before anything happens
    """

    connection = sqlite3.connect(APP_DATABASE_NAME)
    cursor = connection.cursor()

    cursor.executescript(
        """
        BEGIN;
        CREATE TABLE IF NOT EXISTS tasks (
            hash TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            type INTEGER NOT NULL
        ) WITHOUT ROWID;
        COMMIT;
    """
    )


if __name__ == "__main__":
    set_up_database()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # we enter a never-ending loop that waits for data and runs
    # callbacks whenever necessary.
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt. Bye!")
