#-------------------------------------------------------------------------------
# Name:        AMQP API
# Purpose:     Simplify pika usage
#
# Author:      kristjan.vilgo
#
# Created:     09.10.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pika


def create_connection(username, password, host, port, virtual_host, logger):
    """Create connection and channel to rabbit
    return: {connection, channel, info}"""

    connection_result = {}

    authentication          = pika.PlainCredentials(username, password)
    connection_parameters   = pika.ConnectionParameters(host=host,
                                                        port=port,
                                                        virtual_host=virtual_host,
                                                        credentials=authentication)

    try:
        # Start a connection
        connection = pika.BlockingConnection(connection_parameters)
        connection_result["connection"] = connection

        # Start a channel (automatic)
        channel = connection.channel()
        connection_result["channel"] = channel

        # Add status debug info
        info_message = f"Connection made to {host}:{port} for {username}"
        logger.info(info_message)
        connection_result["info"] = info_message

    except Exception as error:

        connection_result["connection"] = None

        connection_result["channel"] = None

        # Add status debug info
        info_message = f'Failed to create connection to {host}:{port} for {username} -> {error}'
        logger.error(info_message)
        connection_result["info"] = info_message

    return connection_result


def send_message(message, url, virtual_host, routing_key, logger, username="quest", password="quest", port=5672, exchange=""):
    """Create session to RabbitMQ and send one message to XMLExchange with defined routing key"""

    # Dictionary to keep all the infomration realted to message delivery
    message_info = {}
    message_info["exchange"] = exchange
    message_info["routing_key"] = routing_key
    message_info["routed"] = False

    # Create connection and channel
    connection_status = create_connection(username, password, url, port, virtual_host, logger)

    connection = connection_status["connection"]
    channel = connection_status["channel"]

    # Connection status info
    message_info["connection_info"] = connection_status["info"]

    if connection:

        # Turn on delivery confirmations
        channel.confirm_delivery()

        # Send message
        logger.info(f"Exchange: {exchange}, RoutingKey: {routing_key}")



        try:
            channel.basic_publish(exchange=exchange,
                                  routing_key=routing_key,
                                  body=message,
                                  properties=pika.BasicProperties(content_type='text/xml'),
                                  mandatory=True)

            logger.info('Message sent - Routing OK')
            message_info["routed"] = False

        except pika.exceptions.UnroutableError:

            logger.error('Message not sent - Routing NOK')

        # Close connection
        connection.close()

    return message_info


def get_message(que, url, virtual_host, logger, username="quest", password="quest", port=5672, auto_ack=False):
    """Create session to RabbitMQ and get one message from defined que"""

    # Object to keep message info
    message_info = {"que_name": que,
                    "body": ""}

    # Create connection and channel
    connection_status = create_connection(username, password, url, port, virtual_host, logger)

    connection = connection_status["connection"]
    channel = connection_status["channel"]

    # Connection status info
    message_info["connection_info"] = connection_status["info"]

    if connection:

        logger.info("Getting message from que: {}".format(que))

        # Get que size before requesting message
        que_object = channel.queue_declare(que, passive=True)  # Get que object if exists
        que_size = que_object.method.message_count
        message_info["que_size"] = que_size

        logger.info("Number of messages in que: {}".format(que_size))

        if que_size == 0:
            logger.warning("No messages in que {}".format(que))

            # Close connection
            connection.close()

            return message_info

        # Get message from que
        method_frame, header_frame, body = channel.basic_get(que, auto_ack=auto_ack)

        message_info["method_frame"] = method_frame

        if body:
            message_info["body"] = body.decode()
        else:
            logger.warning("Empty message returned")
            message_info["body"] = ""

        if method_frame:
            message_info["header_frame"] = header_frame.__dict__
            logger.info(f"Message received: {message_info['header_frame']}")
        else:
            logger.error("No message returned")

        # Close connection
        connection.close()

    return message_info
