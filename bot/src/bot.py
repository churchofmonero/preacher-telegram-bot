#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from datetime import datetime, timedelta

from pymongo import DESCENDING, ReturnDocument

from utils import (
    get_emoji_value, validate_username, 
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

        emoji_faith = get_emoji_value(user['faith'])
        ret += emoji_faith + '🙏'
        logger.info("Adding %d spaces" % (longest_faith - len(str(user['faith']))))

        # string.format() doesn't work OK with TG & emojis
        ret += 6 * (longest_faith - len(str(user['faith'])) + 1) * ' '

        # fix padding for single-digit faiths
        if len(str(user['faith'])) % 3 != 0:
            ret += ' '

        ret += '@' + user['username'] + '\n'

    logger.info(ret)
    return ret


def get_top_heart():
    top_churchgoers_header = 'TOP CHURCHGOERS by heart:\n\n'
    ret = top_churchgoers_header
    longest_heart = 0
    users = disciples.find(sort=[('heart', DESCENDING)])

    if users.count() == 0:
        return "There's no kind people at all..."

    for user in users:
        len_faith = len(str(user['heart']))
        if longest_heart < len_faith:
            longest_heart = len_faith
    users.rewind()

    for user in users:
        if user['heart'] <= 0:
            continue

        emoji_faith = get_emoji_value(user['heart'])
        ret += emoji_faith + '❤️'
        logger.info("Adding %d spaces" % (longest_heart - len(str(user['heart']))))

        # string.format() doesn't work OK with TG & emojis
        ret += 6 * (longest_heart - len(str(user['heart'])) + 1) * ' '

        # fix padding for single-digit faiths
        if len(str(user['heart'])) % 3 != 0:
            ret += ' '

        ret += '@' + user['username'] + '\n'

    logger.info(ret)
    return ret


def init_user(user):
    new_disciple = {
        'tg_user_id': user.id,
        'username': user.username,
        'username_lower': user.username.lower(),
        'faith': 0,
        'heart': 0,
    }

    disciples.save(new_disciple)
    #disciples.insert_one(new_disciple)


def update_user(tg_user_id, field, amount):
    if field not in ['heart', 'faith']:
        raise Exception('Unknown field %s' % field)

    disciples.find_one_and_update(
        {'tg_user_id': tg_user_id},
        {'$inc': {
             field: amount,
         }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )


def change_field(user=None, field='', amount=0):
    if not user:
        logger.error('User is empty/None, cannot change %s' % field)
        return

    try:
        amount = int(amount)
    except TypeError:
        error = 'Invalid integer: "%s"' % str(amount)
        logger.error(error)
        return error 

    if user.username == BOT_USERNAME:
        return 'SELF'
    
    if disciples.count_documents({'tg_user_id': user.id}) == 0:
        logger.info('no result, creating @%s, uid: %d' % (user.username, user.id))
        init_user(user)
        update_user(user.id, field, amount)
    else:
        update_user(user.id, field, amount)

    return 'SUCCESS'


def typing_action(message, seconds=0.2):
    bot.send_chat_action(message.chat.id, 'typing')
    sleep(seconds)


def get_field(field, user):
    logger.debug('get_%s: %s' % (field, user.id))
    user = disciples.find_one({'tg_user_id': user.id})

    if not user:
        disciples.find_one_and_update(
            {'tg_user_id': user.id},
            {'$set': {
                 'faith': 1 if field == 'faith' else 0,
                 'heart': 1 if field == 'heart' else 0,
                 'tg_user_id': user.id,
                 'username': user.username,
                 'username_lower': user.username.lower()
             }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return 0

    if field not in user:
        raise Exception('No such field: %s' % field)

    return user[field]


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


def change_field_with_reply(message, field):
    black_heart = '🖤'

    if message.text not in '❤️🖤+🙏-🔥':
        return

    username = message.from_user.username
    reply_to_user = message.reply_to_message.from_user

    if field == 'heart':
        amount = 1
        if black_heart in message.text:
            amount = -1

        ret = change_field(reply_to_user, 'heart', amount)
        if ret == 'SUCCESS':
            emoji_heart = get_emoji_value(get_field('heart', reply_to_user))
            change = 'increased' if black_heart not in message.text else 'decreased'
            safe_reply(message, "@%s has %s @%s's Heart! It is now %s" % (username, change, reply_to_user.username, emoji_heart))
        return

    admins = bot.get_chat_administrators(message.chat.id)
    if username not in list([a.user.username for a in admins]):
        logger.info('@%s has tried to change the faith of @%s'
                    ', but he is not a pastor.' % (username, reply_to_user.username))
        return

    logger.info('@%s is changing @%s\'s %s' % (username, reply_to_user.username, field))

    if message.text in '+🙏':
        ret = change_field(reply_to_user, 'faith', 1)
        if ret == 'SUCCESS':
            emoji_faith = get_emoji_value(get_field('faith', reply_to_user))
            safe_reply(message, "@%s has increased @%s's Faith! It is now %s" % (username, reply_to_user.username, emoji_faith))
    # elif message.text in '-🔥':
    #     ret = change_field(reply_to_user, 'faith', -1)
    #     if ret == 'MINIMUM FAITH':
    #         safe_reply(message, '@%s does not have any faith in his heart! 😭' % reply_to_user.userrname)
    #     elif ret == 'SUCCESS':
    #         safe_reply(message, "@%s has decreased @%s's Faith! Shame!" % (username, reply_to_user.username))


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


@bot.message_handler(commands=['topheart'])
def top_heart_command(message):
    top_heart = get_top_heart()
    safe_reply(message, top_heart)  #, parse_mode='html')


# Main message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    logger.info(message.text.encode('utf-8').decode('utf-8'))
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        if message.text in '❤️🖤':
            change_field_with_reply(message, 'heart')
        else:
            change_field_with_reply(message, 'faith')
    elif message.text == '!topfaith':
        top_faith_command(message)
    elif message.text == '!topheart':
        top_heart_command(message)

    logger.info("%d, @%s (%d): %s" % (message.chat.id, message.from_user.id, message.from_user.username, message.text))

bot.polling(none_stop=True)
connection.close()

