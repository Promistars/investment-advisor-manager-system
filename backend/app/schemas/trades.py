from pydantic import BaseModel


class TradesPayload(BaseModel):
    trades: list[dict]
