# PreacherBot
Preacherbot is a community developed Telegram bot that facilitates the weekly Church of Monero Mass.

## Installation
`docker-compose build`

## Running
First, you will need to export the following environment variables:

`PREACHER_TELEGRAM_TOKEN` - your Telegram bot's access token

`MONGO_INITDB_ROOT_USERNAME` (optional, defaults to "root")

`MONGO_INITDB_ROOT_PASSWORD` (optional, defaults to "default_password")


Then start the container in the background:

`docker-compose up -d`
