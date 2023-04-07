from pydantic import BaseModel
from typing import List, Optional


class Interface(BaseModel):
    input: List
    output: List


class Config(BaseModel):
    title: str = ""
    version: str = ""
    description: str = ""
    copyright: str = ""
    interface: Interface
