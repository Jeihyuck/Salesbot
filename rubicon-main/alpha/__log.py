import logging
from alpha.settings import VITE_OP_TYPE
from logging.handlers import RotatingFileHandler
import pprint
import rich
import functools
import sys
from rich.style import Style
from rich.console import Console

from icecream import ic

# from dill.source import getname

console = Console()


if VITE_OP_TYPE == "PROD":
    write_to_logfile = True
else:
    write_to_logfile = False

try:
    logger = logging.getLogger(__name__)
    streamHandler = logging.StreamHandler()
    fileHandler = RotatingFileHandler(
        "/www/alpha/__log/alpha.log", maxBytes=4096 * 1000, backupCount=10
    )
    fileHandler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] >> %(message)s")
    )
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    logger.setLevel(logging.DEBUG)

except Exception:
    write_to_logfile = False



# def get_var_name(variable):
#     globals_dict = globals()
#     print(globals_dict)
#     return [var_name for var_name in globals_dict if globals_dict[var_name] is variable]

DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat

# def debug(text, message, locals=False):
#     if write_to_logfile:
#         logger.debug(text + ' :', str(message))
#     else:
#         if locals == False:
#             console.log(text + ' :')
#             console.log(message)
#         else:
#             console.log(text + ' :', message, log_locals=True)
#             console.log(text + ' :', message, log_locals=True)
# def debug(message, locals=False):
#     if write_to_logfile:
#         logger.debug(message)
#     else:
#         if locals == False:
#             console.log(message)
#         else:
#             console.log(message, log_locals=True)

def debug(message = None):
    if write_to_logfile:
        logger.debug(message)
    else:
        console.log(message)
        
def info(message = None):
    if write_to_logfile:
        logger.info(message)
    else:
        console.log(message)

def error(message = None):
    if write_to_logfile:
        logger.error(message)
    else:
        # console.print(message, style = Style.parse("red"))
        console.print_exception(extra_lines=2)

def inspect(obj):
    rich.inspect(obj, methods = True)

