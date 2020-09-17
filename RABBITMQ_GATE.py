#-------------------------------------------------------------------------------
# Name:        RABBITMQ XML GATE
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     29.07.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPL V2
#-------------------------------------------------------------------------------

import os
import sys
import base64
import configparser
import logging

from flask import Flask, request
from flask_restplus import Api, Resource, reqparse, abort

import amqp_API


def parse_basic_auth(auth_header_string):
    """Simple parser to parse authentication"""
    base64_encoded_token = auth_header_string.split(" ")[1].encode()
    username, password = base64.b64decode(base64_encoded_token).decode().split(":")

    return username, password


# Create Flask application
application = Flask(__name__)


# Set GUNICORN WSGI logging (deployment uses GUNICORN)
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    application.logger.handlers = gunicorn_logger.handlers
    application.logger.setLevel(gunicorn_logger.level)

else:
    #logger = logging.getLogger()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)


# SETTINGS - START

# Parse settings
raw_settings = configparser.RawConfigParser()

raw_settings.read("application.properties")

settings_dict = {}
for setting in raw_settings.items("Main"):

    parameter_name, parameter_default_value = setting

    # First, lets see if parameter is defined in ENV
    parameter_value = os.getenv(parameter_name)

    # if parameter is defined in ENV
    if parameter_value:
        settings_dict[parameter_name] = parameter_value

    else:
        settings_dict[parameter_name] = parameter_default_value
        application.logger.info(f"Parameter {parameter_name} not defined in ENV using default value from application.config -> {parameter_default_value}")

server   = settings_dict['rmq_server']
port     = int(settings_dict['rmq_amqp_port'])
vhost    = settings_dict['rmq_vhost']
exchange = settings_dict['rmq_exchange']

application.logger.info(f"Starting service with conf -> {settings_dict}")


# SETTINGS - END


api = Api(app=application,
          version='0.2',
          title="RABBITMQ XML GATE",
          description='REST API for sending and receiving XML messages over RabbitMQ')

# Main namespace for XML exchange
xml_exchange = api.namespace("XMLExchange", description="Send XML data over RabbitMQ")

# Lets define send message XML parser
xml_exchange_send_parser = reqparse.RequestParser()
xml_exchange_send_parser.add_argument("routing_key", type=str, required=True, default="test_routing_key")  # , choices = routing_keys)
# xml_exchange_send_parser.add_argument("Content-Type", required = True, location='headers', choices = ["text/xml"])
xml_exchange_send_parser.add_argument("Authorization", required=True, location='headers', default="Basic Z3Vlc3Q6Z3Vlc3Q=")

# TODO - error handling
@xml_exchange.route("/send_message")
class SendXML(Resource):

    @api.expect(xml_exchange_send_parser, validate=True)
    def post(self):
        """Add XML file as plain text/xml to the POST body"""

        # Use only for DEBUG, contains log who accessed and from where
        application.logger.info(f"FROM:{request.remote_user}@{request.remote_addr} "
                                 f"METHOD:{request.method} "
                                 f"HEADERS:{dict(request.headers)}")

        # Parse arguments
        args = xml_exchange_send_parser.parse_args()

        # Parse credentials
        try:
            username, password = parse_basic_auth(args["Authorization"])
        except:
            message = "Authentication parsing failed, expected mime content is: 'Authorization: Basic base64(<username>:<password>)'"
            application.logger.error(message)
            abort(401, message)

        application.logger.info(f"Sending message with routing key {args['routing_key']} to {server}")


        status = amqp_API.send_message(request.data.decode(), server, vhost, args["routing_key"], application.logger, username, password, port=port, exchange=exchange)


        status["user"] = username



        if status["routed"] and status["connection"]:
            application.logger.info(status)
        else:
            application.logger.error(status)
            status.pop("connection")
            status.pop("channel")

            abort(400, status)

        status.pop("connection")
        status.pop("channel")

        return status


# Lets define get message XML parser
xml_exchange_get_parser = reqparse.RequestParser()
xml_exchange_get_parser.add_argument("queue_name", type=str, required=True, default="test_que")  # , choices = queue_names)
xml_exchange_get_parser.add_argument("Authorization", required=True, location='headers', default="Basic Z3Vlc3Q6Z3Vlc3Q=")


# TODO - error handling
@xml_exchange.route("/get_message")
class GetXML(Resource):

    @api.expect(xml_exchange_get_parser, validate=True)
    def get(self):
        """Get XML file as plain text/xml in the GET response body"""

        # Use only for DEBUG, contains log who accessed and from where
        application.logger.info(f"FROM:{request.remote_user}@{request.remote_addr} "
                                 f"METHOD:{request.method} "
                                 f"HEADERS:{dict(request.headers)} ")

        # Parse args
        args = xml_exchange_get_parser.parse_args()

        try:
            username, password = parse_basic_auth(args["Authorization"])
        except:
            message = "Authentication parsing failed, expected mime content is: 'Authorization: Basic base64(<username>:<password>)'"
            application.logger.error(message)
            abort(400, message)

        application.logger.info(f"{username} requesting message from {args['queue_name']}")

        message = amqp_API.get_message(args["queue_name"], server, vhost, application.logger, username, password, port=port, auto_ack=True)

        if message["connection"]:
            application.logger.info(message)
            return message["body"]

        else:
            application.logger.error(message)
            message.pop("connection")
            message.pop("channel")
            abort(400, message)
            return message


if __name__ == '__main__':
    application.run(debug=True, port=80)


# TODO - log xml message header
### Lets get root element and its namespace
##namesapce, root = xml.tag.split("}")
##properties_dict["root"] = root
##properties_dict["namespace"] = namesapce[1:]
##
### Lets get all children of root
##for element in xml.getchildren():
##    # If element has children then it is not root meta field
##    if len(element.getchildren()) == 0:
##        # If not, then lets add its anme and value to properties
##        properties_dict[element.tag.split("}")[1]] = element.text

