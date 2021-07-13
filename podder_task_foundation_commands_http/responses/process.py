from pydantic import BaseModel


class Process(BaseModel):
    name: str = ""
