FROM debian:9
ENV DEBIAN_FRONTEND noninteractive

ARG PREACHER_TELEGRAM_TOKEN
ENV PREACHER_TELEGRAM_TOKEN=${PREACHER_TELEGRAM_TOKEN}

WORKDIR /app

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip python3-setuptools

COPY requirements.pip .
RUN pip3 install -r requirements.pip

COPY src/bot.py .
COPY wait-for-it.sh .

CMD ["./wait-for-it.sh", "db:27017", "--", "./bot.py"]

