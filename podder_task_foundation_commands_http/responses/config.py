from pydantic import BaseModel


class Config(BaseModel):
    title: str = ""
    version: str = ""
    description: str = ""
    copyright: str = ""
