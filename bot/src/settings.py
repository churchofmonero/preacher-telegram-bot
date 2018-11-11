import logging
from telebot import TeleBot, util
from pymongo import MongoClient
from os import getenv as os_getenv
from sys import argv as sys_argv

def load_env(env_name):
    ret = os_getenv(env_name)
    if not ret:
        logger.error('%s environment variable is unset!' % env_name)
        exit(1)
    return ret

# Logging config
FORMAT = '%(asctime)s -- %(levelname)s -- %(module)s %(lineno)d -- %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('preacher')
logger.info("Running %s" % sys_argv[0])

BOT_USERNAME = 'XMR_Preacher_Bot'
TELEGRAM_API_MAX_CHARS = 4000

ACCESS_TOKEN = load_env('PREACHER_TELEGRAM_TOKEN')
GROUP_ID = load_env('PREACHER_GROUP_ID')

MONGO_USER = load_env('MONGO_INITDB_ROOT_USERNAME')
MONGO_PASS = load_env('MONGO_INITDB_ROOT_PASSWORD')

docker_mongo_service = 'mongo_db'
host, port = (docker_mongo_service, 27017)

logger.info("Connecting to %s:%d" % (host, port))
client = MongoClient('mongodb://%s:%s@%s:%d' % (MONGO_USER, MONGO_PASS, host, port))
db = client['MoneroChurch']
disciples = db['Disciple']

# Make 'tg_user_id' field unique
tg_user_id_index = 'tg_user_id'
if tg_user_id_index not in disciples.index_information():
    disciples.create_index('tg_user_id', unique=True)

bot = TeleBot(ACCESS_TOKEN)

