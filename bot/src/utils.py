from settings import logger

# Map integers to nice emojis
EMOJI_INT = {
        '-': '➖',
        '0': '0⃣',
        '1': '1️⃣',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣',
}

def get_emoji_faith(faith: int):
    emoji_faith = ''
    for ch in str(max(0, faith)):
        emoji_faith += EMOJI_INT[ch]
    return emoji_faith


def sanitize(string):
    return string.replace('--', '').replace(';', '')[:100]


def validate_username(username: str):
    max_len, min_len = (5, 16)
    if not username:
        return 'Username cannot be empty!'

    if len(username) < min_len:
        return 'Username should be at least %d characters long!' % min_len
    elif len(username) > max_len:
        return 'Username cannot be longer than %d characters!' % max_len

    allowed_chars = 'abcdefghijklmnopqrstuvwxyz_'
    if any(ch not in allowed_chars for ch in username.lower()):
        return 'Username contains invalid characters!'

