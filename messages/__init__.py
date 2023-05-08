from messages.messages import msgs
from messages.messages import main_keyboard


def get_message_text(msg_name, *args, **kwargs):
    return msgs.get(msg_name, "UNKNOWN_MESSAGE").format(*args, **kwargs)
