from typing import List

from pydantic import BaseModel

from .process import Process


class Processes(BaseModel):
    processes: List[Process] = []
