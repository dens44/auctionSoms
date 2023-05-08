API_TOKEN = "BAD TOKEN"

NEED_SAVE_LOGS_TO_FILE = True

# for locally rewrite settings add it to settings_local.py
try:
    from settings_local import *
except ModuleNotFoundError as err:
    pass
