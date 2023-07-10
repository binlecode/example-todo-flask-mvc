FROM python:3.10-alpine

RUN adduser -D todosmvc

WORKDIR /home/todosmvc

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY mvc mvc
COPY boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP mvc

RUN chown -R todosmvc:todosmvc ./
USER todosmvc

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]