from argparse import Namespace
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from podder_task_foundation.commands.command import Command
from podder_task_foundation.context import Context
from podder_task_foundation.parameters import Parameters
from podder_task_foundation import bootstrap

from .handlers import ProcessesHandler, ProcessHandler, ConfigHandler
from .responses import Processes, Config


class Http(Command):
    name = "http"
    help = "Build HTTP server with process API"
    mode = "HTTP"

    def __init__(self):
        self._context = None
        self._mode = "http"

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
        parser.add_argument('-w',
                            '--workers',
                            nargs='?',
                            default=4,
                            type=int,
                            help='Number of workers')
        parser.add_argument('-c',
                            '--config',
                            nargs='?',
                            default="",
                            type=str,
                            help='Config file path')

    def handler(self, arguments: Namespace, unknown_arguments: Parameters,
                *args):
        self._context = Context(mode=self._mode,
                                config_path=arguments.config,
                                verbose=arguments.verbose,
                                logger=logger,
                                debug_mode=arguments.debug)
        bootstrap(self._context)
        application = self._create_app(self._context)
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        routers = self._routers()
        application.mount(
            "/static",
            StaticFiles(
                directory=str(Path(__file__).parent.joinpath("static"))),
            name="static")

        @application.get("/", response_class=HTMLResponse)
        async def index():
            template_directory = Path(__file__).parent.joinpath("templates")
            return template_directory.joinpath("index.html").read_text("utf-8")

        @application.get("/healthz", response_class=HTMLResponse)
        async def index():
            return {"status": True}

        application.include_router(routers, prefix="/api")
        log_level = "info"
        if arguments.debug:
            log_level = "debug"
        workers = arguments.workers if arguments.workers > 0 else None
        uvicorn.run(application,
                    host=arguments.host,
                    port=arguments.port,
                    workers=workers,
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
            "/config",
            response_model=Config,
            name="get-config",
        )
        async def get_config() -> Config:
            context = self._create_context(None)
            return ConfigHandler().handle(context)

        @router.post(
            "/entrypoint",
            response_model=Processes,
            name="processes:exec-entry-point",
        )
        async def post_entrypoint(request: Request):
            output_name = request.query_params.get("output_name")
            process_name = self._context.config.get(
                "plugins.commands.http.entrypoint.process")
            if process_name is None:
                raise HTTPException(status_code=400,
                                    detail="No entrypoint defined")

            context = self._create_context(None)
            form = await request.form()
            return ProcessHandler().handle(context=context,
                                           name=process_name,
                                           _input=form,
                                           output_name=output_name)

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
                                           _input=form,
                                           output_name=output_name)

        return router
