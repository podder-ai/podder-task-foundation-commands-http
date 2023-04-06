from podder_task_foundation.context import Context

from ..responses import Config


class ConfigHandler(object):
    @staticmethod
    def handle(context: Context) -> Config:
        return Config(**{
            "name": context.config.get("plugins.commands.http.config.name"),
            "version": context.version,
            "description": context.config.get("plugins.commands.http.config.description")
        })
