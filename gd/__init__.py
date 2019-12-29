"""Library that provides its users ability to interact with servers of Geometry Dash."""

__title__ = 'gd'
__author__ = 'NeKitDS'
__copyright__ = 'Copyright 2019 NeKitDS'
__license__ = 'MIT'
__version__ = '0.10.3'

from collections import namedtuple
import logging
import re

from .abstractentity import AbstractEntity
from .abstractuser import AbstractUser, LevelRecord
from .client import Client
from .colors import Colour, Color
from .colors import colors
from .comment import Comment
from .errors import *
from .friend_request import FriendRequest
from .iconset import IconSet
from .level import Level
from .level_packs import Gauntlet, MapPack
from .message import Message
from .session import GDSession
from .song import Song
from .unreguser import UnregisteredUser
from .user import UserStats, User
from .events import exit  # idk
from .utils.enums import *
from .utils.filters import Filters
from .utils.gdpaginator import paginate, Paginator
from .utils.http_request import http, HTTPClient
from .utils.params import *
from .utils.save_parser import Save, SaveParser
from .utils.crypto.coders import Coder
from .utils.crypto.xor_cipher import XORCipher

from ._jokes import jokes  # why not?...

from .utils._async import synchronize
from .utils import tasks

from . import (
    api,     # non-server GD API.
    events,  # event-related functions and classes.
    utils    # different useful utils.
)


log = logging.getLogger(__name__)


VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

RegularExpression = r"""
^\s*
(?:
    (?P<major>\d+)
    (?P<split>[\.-])?
    (?P<minor>\d+)?
    (?P=split)?
    (?P<micro>\d+)?
    (?P<releaselevel>a|b|rc|f|dev)?
    (?P<serial>\d+)?
)
\s*$
"""
CompiledRE = re.compile(re.sub(r'\s', '', RegularExpression), re.MULTILINE)

def make_version_details(ver: str):
    match = CompiledRE.match(ver)

    if match is None:
        return VersionInfo(0, 0, 0, 'final', 0)

    args = {}

    for key, value in match.groupdict().items():
        if key == 'split':
            continue

        elif key == 'releaselevel':
            if value is None:
                value = 'f'

            value = {
                'a': 'alpha',
                'b': 'beta',
                'rc': 'release_candidate',
                'f': 'final',
                'dev': 'developer'
            }.get(value, 'final')

        elif value is None:
            value = 0

        else:
            value = int(value)

        args[key] = value

    return VersionInfo(**args)

version_info = make_version_details(__version__)


def setup_logging(level: int = logging.DEBUG, *, stream=None, file=None, formatter=None):
    """Function that sets up logs of the module.

    Parameters
    ----------
    level: :class:`int`
        Level to set.

    stream: `Any`
        Stream to log messages into. ``stderr`` by default.

    file: `Any`
        File to log messages to. If not given, messages are logged into the ``stream``.

    formatter: :class:`str`
        Formatter to use. ``[LEVEL] (time) {gd.module}: Message`` by default.
    """
    handler = (
        logging.StreamHandler(stream) if file is None else logging.FileHandler(file)
    )

    if formatter is None:
        formatter = '[%(levelname)s] (%(asctime)s) {%(name)s}: %(message)s'

    handler.setFormatter(
        logging.Formatter(formatter)
    )

    log.addHandler(handler)

    log.setLevel(level)

# setting up the NullHandler here
try:
    from logging import NullHandler

# in case there is no NullHandler
except ImportError:  # pragma: no cover
    # create custom class
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

log.addHandler(NullHandler())


# delete not required stuff
del NullHandler, namedtuple, re
