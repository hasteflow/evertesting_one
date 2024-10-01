import logging
from datetime import timedelta

# logging info
APP_LOG_NAME = "eValidator"
APP_LOG_LEVEL = logging.DEBUG

APP_AMQP = {
    "url": "amqp://guest:guest@localhost//",
    "queue_name": "eValidator_queue",
    "error_queue_name": "eValidator_queue_ERROR",
    "routing_key": "eValidator-ERROR",
    "exchange_name": "eExchange",
}

APP_EVENT_ATTRIBUTES = {
    "type": "com.evertest.event",
    "source": "evalidator",
    "subject": "ERROR",
    "datacontenttype": "application/json",
}

# have it as timedelta for explicitness
# TODO: change to reading from environ
VALIDATION_WINDOW_MS = timedelta(milliseconds=1000)
