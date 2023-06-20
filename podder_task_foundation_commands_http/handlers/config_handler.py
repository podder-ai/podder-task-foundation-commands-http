from podder_task_foundation.context import Context

from ..responses import Config, Interface


class ConfigHandler(object):

    @staticmethod
    def handle(context: Context) -> Config:
        _input = context.config.get(
            "plugins.commands.http.config.interface.input", [])
        _output = context.config.get(
            "plugins.commands.http.config.interface.output", [])
        return Config(
            **{
                "title":
                context.config.get("plugins.commands.http.config.title"),
                "version":
                context.version,
                "description":
                context.config.get("plugins.commands.http.config.description"),
                "interface":
                Interface(**{
                    "input": _input,
                    "output": _output,
                })
            })
