from typing import List, Optional

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from podder_task_foundation.commands.command import Command
from podder_task_foundation.context import Context

from .handlers import ProcessesHandler, ProcessHandler
from .responses import Processes


class Http(Command):
    name = "http"
    help = "Build HTTP server with process API"
    mode = "HTTP"

    def __init__(self):
        self._context = None

    def set_arguments(self, parser):
        parser.add_argument('-v',
                            '--verbose',
                            dest='verbose',
                            action='store_true',
                            help='Set verbose mode')
        parser.add_argument('-d',
                            '--debug',
                            dest='debug',
                            action='store_true',
                            help='Enable debug mode')
        parser.add_argument('-H',
                            '--host',
                            nargs='?',
                            default="127.0.0.1",
                            type=str,
                            help='Host address')
        parser.add_argument('-p',
                            '--port',
                            nargs='?',
                            default=5000,
                            type=int,
                            help='Port number')
        parser.add_argument(
            '-c',
            '--config',
            nargs='?',
            default="",
            type=str,
            help='Input files (you can pass file[s] or directory)')

    def handler(self, arguments):
        self._context = Context(mode=self.mode,
                                config_path=arguments.config,
                                verbose=arguments.verbose,
                                debug_mode=arguments.debug)

        application = self._create_app(self._context)
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        routers = self._routers()
        application.include_router(routers, prefix="/api")
        log_level = "info"
        if arguments.debug:
            log_level = "debug"
        uvicorn.run(application,
                    host=arguments.host,
                    port=arguments.port,
                    log_level=log_level)

    @staticmethod
    def _create_app(context: Context) -> FastAPI:
        application = FastAPI(title="Podder HTTP API Server",
                              debug=context.debug_mode,
                              version=context.version)
        return application

    def _create_context(self, name: Optional[str] = None) -> Context:
        context = Context(mode=self._context.mode,
                          process_name=name,
                          config_path=self._context.config.path,
                          debug_mode=self._context.debug_mode)

        return context

    def _routers(self) -> APIRouter:
        router = APIRouter()

        @router.get(
            "/processes",
            response_model=Processes,
            name="processes:get-process-list",
        )
        async def get_process_list() -> Processes:
            context = self._create_context(None)
            return ProcessesHandler().handle(context)

        @router.post(
            "/processes/{process_name}",
            response_model=Processes,
            name="processes:exec-process",
        )
        async def execute_process(process_name: str, request: Request):
            output_name = request.query_params.get("output_name")
            context = self._create_context(None)
            form = await request.form()
            return ProcessHandler().handle(context=context,
                                           name=process_name,
                                           files=form,
                                           output_name=output_name)

        return router
