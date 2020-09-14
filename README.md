# RABBIT_XML_GATE

REST API for sending and receiving XML messages over RabbitMQ

### Install
Use provided install.sh or install.bat or

`python -m pip install pipenv`

`python -m pipenv install`

### Run
1. Change content of application.properties
2. Use provided run.sh or run.bat

`pipenv run python RABBITMQ_GATE.py`  

    
### Docker
1. Build and name image (tag is used for naming)
2. Run image by it's name and set application properties as env (--publish <external_port>:<internal_port> --env rmq_server=127.0.0.1)



`docker build . --tag rabbit_xml_gate`

`docker run --detach --publish 80:80 --env rmq_server=127.0.0.1 --env rmq_amq_port=5672 --env rmq_exchange=XMLExchange --env rmq_vhost=/ rabbit_xml_gate`


    