import logging

# API version. changes module loading and routes prefix as well
API_VERSION = "v1"
APP_ROUTES_PACKAGE_NAME = f"api.{API_VERSION}.routes"

# {module_name: route_prefix}
APP_ROUTES = {"data": f"/api/{API_VERSION}/data"}
APP_PORT = 8000

# logging info
APP_LOG_NAME = "eReceiver"
APP_LOG_LEVEL = logging.DEBUG

APP_EVENT_ATTRIBUTES = {
    "type": "com.evertest.event",
    "source": "ereceiver",
    "subject": "DATA",
    "datacontenttype": "application/json",
}

APP_AMQP = {
    # "url": "amqp://guest:guest@localhost//",
    "url": "amqp://user:user@rabbitmq:5672//",
    "queue_names": {
        "eProcessor": "ePublisher_queue",
        "eValidator": "eValidator_queue",
    },
    "exchange_name": "eExchange",
    "exchange_type": "fanout",
    "routing_key": "does_not_matter_for_fanout",
}
