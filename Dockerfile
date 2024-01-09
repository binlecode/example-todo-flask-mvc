FROM python:3.10-alpine

RUN adduser -D todosmvc

WORKDIR /home/todosmvc

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY mvc mvc
COPY boot.sh ./
COPY config.py ./
RUN chmod +x boot.sh

ENV FLASK_APP mvc
# set LOG_LEVEL from env var or use default if not given
# this env var is used in both config.py and boot.sh
ENV LOG_LEVEL=info
# set SCRIPT_NAME from env var or use default if not given
ENV SCRIPT_NAME=todo-flask-mvc

RUN chown -R todosmvc:todosmvc ./
USER todosmvc

CMD ["./boot.sh"]
