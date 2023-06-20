from podder_task_foundation.context import Context

from ..responses import Process, Processes


class ProcessesHandler(object):

    @staticmethod
    def handle(context: Context) -> Processes:
        processes = context.processes
        result = []
        for name, interface in processes.items():
            result.append(Process(**{"name": name}))
        return Processes(**{"processes": result})
