import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db_manager as db
from app.deps import get_current_user
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/accounts/{account_name}/commentaries", tags=["commentaries"])

_FONT_CSS = """
<style>
.magic-font-kaiti { font-family: 'KaiTi', 'STKaiti', '楷体', serif !important; }
.magic-font-songti { font-family: 'SimSun', 'STSong', '宋体', serif !important; }
.magic-font-heiti { font-family: 'SimHei', 'STHeiti', '黑体', sans-serif !important; }
.magic-font-yahei { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important; }
.magic-font-times { font-family: 'Times New Roman', Times, serif !important; }
</style>
"""


def apply_magic_format(raw_text: str) -> str:
    if not raw_text:
        return ""
    res = re.sub(
        r"\[([^\]]+)\]\((http[^)]+)\)",
        r'<a href="\2" target="_blank" style="color: #3b82f6; text-decoration: underline;">\1</a>',
        raw_text,
    )
    font_map = {
        "楷体": "magic-font-kaiti",
        "宋体": "magic-font-songti",
        "黑体": "magic-font-heiti",
        "微软雅黑": "magic-font-yahei",
        "Times": "magic-font-times",
    }

    def _repl(m: re.Match) -> str:
        text, font_name = m.group(1), m.group(2)
        cls = font_map.get(font_name, "")
        return f'<span class="{cls}">{text}</span>' if cls else m.group(0)

    res = re.sub(r"\[([^\]]+)\]\(font:([^)]+)\)", _repl, res)
    return _FONT_CSS + res


class CommentaryBody(BaseModel):
    report_name: str
    html: str


@router.get("")
def list_commentaries(account_name: str, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    return db.get_all_commentaries(user, account_name)


@router.get("/{report_name}")
def get_commentary(account_name: str, report_name: str, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    return {"html": db.get_commentary(user, account_name, report_name)}


@router.put("/{report_name}", response_model=MessageResponse)
def save_commentary(account_name: str, report_name: str, body: CommentaryBody, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    db.save_commentary(user, account_name, report_name, apply_magic_format(body.html))
    return MessageResponse(message="saved")


@router.delete("/{report_name}", response_model=MessageResponse)
def delete_commentary(account_name: str, report_name: str, user: str = Depends(get_current_user)):
    if not db.get_account_id(user, account_name):
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete_commentary(user, account_name, report_name)
    return MessageResponse(message="deleted")
