from pydantic import BaseModel


class AccountSummary(BaseModel):
    name: str
    last_accessed: str | None = None
    principal: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    total_asset: float = 0
    as_of_date: str = ""
    fees_collected: float = 0


class AccountCreateRequest(BaseModel):
    name: str


class StartDateUpdate(BaseModel):
    start_date: str


class FeeTotalResponse(BaseModel):
    total_fees: float
    account_count: int
