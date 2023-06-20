from typing import List, Optional

from pydantic import BaseModel


class Interface(BaseModel):
    input: List
    output: List


class Config(BaseModel):
    title: str = ""
    version: str = ""
    description: str = ""
    copyright: str = ""
    interface: Interface
