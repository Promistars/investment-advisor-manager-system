from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    username: str


class AccountOut(BaseModel):
    name: str
    last_accessed: str | None = None
    snapshot: "SnapshotOut | None" = None


class SnapshotOut(BaseModel):
    principal: float
    total_asset: float
    pnl: float
    pnl_pct: float
    as_of_date: str
    cash: float = 0.0


class CreateAccountRequest(BaseModel):
    name: str


class TradeRow(BaseModel):
    日期: str
    操作类型: str
    标的: str = ""
    数量股: float = Field(0, alias="数量(股)")
    成交单价: float = Field(0, alias="成交单价(¥)")
    实际结算总金额: float = Field(0, alias="实际结算总金额(¥)")

    model_config = {"populate_by_name": True}


class TradesPayload(BaseModel):
    trades: list[dict[str, Any]]


class StartDatePayload(BaseModel):
    start_date: date


class PrefsOut(BaseModel):
    lang: str
    pnl_colors: str
    date_format: str
    compact_ui: bool
    show_emoji: bool
    default_view: str


class PrefsUpdate(BaseModel):
    lang: str | None = None
    pnl_colors: str | None = None
    date_format: str | None = None
    compact_ui: bool | None = None
    show_emoji: bool | None = None
    default_view: str | None = None


class AnalyticsQuery(BaseModel):
    view: Literal["monthly", "quarterly", "yearly", "custom"] = "monthly"
    start: date | None = None
    end: date | None = None


class KpiOut(BaseModel):
    period_return: float
    benchmark_return: float
    alpha: float
    benchmark_price: float
    total_asset: float
    max_drawdown: float
    sharpe_ratio: float
    period_net_inflow: float
    engine_principal: float
    ledger_in: float
    ledger_out: float
    actual_start: str
    actual_end: str


class ChartPoint(BaseModel):
    date: str
    portfolio_return: float
    benchmark_return: float
    total_asset: float
    net_principal: float
    daily_portfolio: float
    daily_benchmark: float


class HoldingOut(BaseModel):
    name: str
    shares: float
    market_value: float
    cost: float | None = None


class AnalyticsOut(BaseModel):
    account: str
    username: str
    mode: Literal["admin", "client"]
    benchmark: str
    account_start_date: str
    global_min_date: str
    global_max_date: str
    max_selectable_date: str
    view_options: list[str]
    view: str
    perf_start: str
    perf_end: str
    kpi: KpiOut
    chart: list[ChartPoint]
    holdings: list[HoldingOut] | None = None
    cash: float
    fees: float
    snap_date: str
    commentary: str | None = None
    commentary_period: str | None = None
    stock_names: list[str] | None = None
    principal_warning: float | None = None


class StockIngestRequest(BaseModel):
    name: str
    force: bool = False


class CommentaryPayload(BaseModel):
    report_name: str
    text: str


class MessageOut(BaseModel):
    message: str
    ok: bool = True
