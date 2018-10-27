#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from datetime import datetime, timedelta

from pymongo import DESCENDING, ReturnDocument

from utils import (
    get_emoji_faith, validate_username, 
)

from settings import (
    logger, client, db, disciples, bot,
    BOT_USERNAME, TELEGRAM_API_MAX_CHARS,
)


def safe_reply(message, reply, parse_mode=None):
    typing_action(message)

    if len(reply) <= TELEGRAM_API_MAX_CHARS:
        bot.reply_to(message, reply, parse_mode=parse_mode)
        return

    # FIXME: splitting text breaks HTML markup.
    # split by lines AND max chars instead
    for splitted_reply in util.split_string(reply, TELEGRAM_API_MAX_CHARS):
        bot.reply_to(message, splitted_reply, parse_mode=parse_mode)
    sleep(0.1)


def get_top_faith():
    top_churchgoers_header = 'TOP CHURCHGOERS:\n\n'
    ret = top_churchgoers_header
    longest_faith = 0
    users = disciples.find(sort=[('faith', DESCENDING)])

    if users.count() == 0:
        return "There's no single believer! We struggle with a lack of faith :("

    for user in users:
        len_faith = len(str(user['faith']))
        if longest_faith < len_faith:
            longest_faith = len_faith
    users.rewind()

    for user in users:
        if user['faith'] <= 0:
            continue

        emoji_faith = get_emoji_faith(user['faith'])
        ret += emoji_faith
        logger.info("Adding %d spaces" % (longest_faith - len(str(user['faith']))))

        # string.format() doesn't work OK with TG & emojis
        ret += 6 * (longest_faith - len(str(user['faith'])) + 1) * ' '

        # fix padding for single-digit faiths
        if len(str(user['faith'])) % 3 != 0:
            ret += ' '

        ret += '@' + user['username'] + '\n'

    logger.info(ret)
    return ret


def change_faith(username='', faith=0):
    if not username:
        logger.error('Empty username, cannot change faith')
        return

    try:
        faith = int(faith)
    except TypeError:
        error = 'Invalid integer: "%s"' % str(faith)
        logger.error(error)
        return error 

    if username == BOT_USERNAME:
        return 'SELF'
    
    logger.info(disciples.count_documents({'username_lower': username.lower()}))
    if disciples.count_documents({'username_lower': username.lower()}) == 0:
        logger.info('no result, creating @%s' % username)

        new_disciple = {
            'username': username,
            'username_lower': username.lower(),
            'faith': 0,
        }

        disciples.insert_one(new_disciple)
    else:
        disciples.update_one(
            {'username_lower': username.lower()},
            {'$inc': {'faith': faith}},
            upsert=True
        )

    return 'SUCCESS'


def typing_action(message, seconds=0.2):
    bot.send_chat_action(message.chat.id, 'typing')
    sleep(seconds)


def get_faith(username):
    logger.debug('get_faith: %s' % username)
    user = disciples.find_one({'username_lower': username.lower()})

    if not user:
        disciples.find_one_and_update(
            {'username_lower': username.lower()},
            {'$set': {
                 'faith': 1,
                 'username': username,
                 'username_lower': username.lower()
             }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return 1

    return user['faith']


@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
def on_user_joins(message):
    new_user_name = message.new_chat_member.username
    logger.info("Detected a new user: @%s, restricting him for two days" % new_user_name)

    bot.restrict_chat_member(
        message.chat.id,
        message.new_chat_member.id,
        until_date=datetime.now() + timedelta(days=2),
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )


def change_faith_with_reply(message):
    if message.text not in '+🙏-🔥':
        return

    username = message.from_user.username
    reply_to_username = message.reply_to_message.from_user.username

    admins = bot.get_chat_administrators(message.chat.id)
    if username not in list([a.user.username for a in admins]):
        logger.info('@%s has tried to change the faith of @%s'
                    ', but he is not a pastor.' % (username, reply_to_username))
        return

    logger.info('@%s is changing @%s\'s faith' % (username, reply_to_username))

    if message.text in '+🙏':
        ret = change_faith(reply_to_username, 1)
        if ret == 'SUCCESS':
            emoji_faith = get_emoji_faith(get_faith(reply_to_username))
            safe_reply (message, "@%s has increased @%s's Faith! It is now %s" % (username, reply_to_username, emoji_faith))
    elif message.text in '-🔥':
        ret = change_faith(reply_to_username, -1)
        if ret == 'MINIMUM FAITH':
            safe_reply (message, '@%s does not have any faith in his heart! 😭' % reply_to_username)
        elif ret == 'SUCCESS':
            safe_reply (message, "@%s has decreased @%s's Faith! Shame!" % (username, reply_to_username))


@bot.message_handler(commands=['getfaith'])
def get_faith_command(message):
    arguments = message.text.split()[1:2]

    if not arguments:
        safe_reply (message, "Usage examples:\n/getfaith UserName\n/getfaith @UserName")
        return

    username = arguments[0].lstrip('@')[:100]

    ret = validate_username(username)
    if ret != True:
        safe_reply (message, ret)
        return

    user = disciples.find_one({'username_lower': username.lower()})
    if not user:
        safe_reply(message, '@%s does not belong to The Church of Monero' % username)
    else:
        emoji_faith = ''
        for ch in str(user['faith']):
            emoji_faith += EMOJI_INT[ch]
        safe_reply(message, 'The Faith of @%s is %s' % (user['username'], emoji_faith))


@bot.message_handler(commands=['changefaith'])
def change_faith_command(message):
    arguments = (message.text.split(' '))[1:3]

    if not arguments:
        safe_reply (message, "Username is missing!\nUsage examples:\n/changefaith UserName 1\n/changefaith @UserName -2")
        return

    if len(arguments) == 1:
        safe_reply (message, "You didn't specify the amount of faith to add/substract")
        sleep(0.2)
        safe_reply (message, "Usage examples:\n/changefaith UserName 1\n/changefaith @UserName -2")
        return

    username = arguments[0].lstrip('@')[:100]

    if not username:
        safe_reply (message, "Username cannot be empty!")
        return

    if len(username) < 5:
        safe_reply (message, "Username should be at least 5 characters long!")
        return

    allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
    if any(ch not in allowed_chars for ch in username):
        safe_reply (message, "Username contains invalid characters!")
        return

    faith = arguments[1]

    try:
        faith = int(faith)
    except ValueError:
        safe_reply(message, '"%s" is not a valid integer!' % str(faith))
        sleep(0.2)
        safe_reply (message, "Usage examples:\n/changefaith UserName 1\n/changefaith @UserName -2")
        return

    ret = change_faith(username, faith)
    if ret == 'SUCCESS':
        safe_reply(message, "@%s's Faith updated by %d. It is now %d." % (username, faith, get_faith(username)))
    elif ret == 'MINIMUM FAITH':
        safe_reply(message, '@%s does not have any faith in his heart anymore! 😭' %username)
    else:
        safe_reply(message, ret)


@bot.message_handler(commands=['getpastors'])
def get_pastors_command(message):
    if message.chat.type == 'private':
        safe_reply(message, 'Meh.')
        return

    admins = bot.get_chat_administrators(message.chat.id)
    if admins:
        ret = ', '.join([a.user.username for a in admins])
        safe_reply(message, ret)
    else:
        safe_reply(message, 'There are no pastors!')


@bot.message_handler(commands=['topfaith'])
def top_faith_command(message):
    top_faith = get_top_faith()
    safe_reply(message, top_faith)  #, parse_mode='html')


# Main message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.reply_to_message:
        change_faith_with_reply(message)

    if message.text == '!topfaith':
        top_faith_command(message)

    logger.info("%d, @%s: %s" % (message.chat.id, message.from_user.username, message.text))

bot.polling(none_stop=True)
connection.close()

