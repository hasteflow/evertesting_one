import logging

# logging info
APP_LOG_NAME = "ePublisher"
APP_LOG_LEVEL = logging.DEBUG

APP_AMQP = {
    # "url": "amqp://guest:guest@localhost//",
    "url": "amqp://user:user@rabbitmq:5672//",
    "queue_name": "ePublisher_queue",
}
APP_DATABASE_NAME = "ePublisher.db"
