__version__ = '0.1.0'

from typing import Type

from podder_task_foundation.commands.command import Command

from .http import Http


def get_class() -> Type[Command]:
    return Http
