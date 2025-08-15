from pydantic import BaseModel


class APIMessage(BaseModel):
    code: str
    message: str

