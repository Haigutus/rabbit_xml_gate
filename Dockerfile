FROM python:3.7

RUN pip install pipenv

WORKDIR /code

# Install needed python modules
COPY Pipfile .
COPY Pipfile.lock .
RUN python -m pipenv install --system --deploy

# Copy needed files
COPY amqp_API.py .
COPY RABBITMQ_GATE.py .
COPY application.properties .
COPY run.sh .

# Tell the port number the container should expose
EXPOSE 80

# run the application
#CMD ["python", "/usr/src/app/app.py"]
CMD ["sh", "./run.sh"]