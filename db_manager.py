# 文件：db_manager.py (数据库驱动模块)
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "trading_system.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    """初始化数据库表结构"""
    with get_conn() as conn:
        cursor = conn.cursor()
        # 1. 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # 2. 投资账户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                last_accessed DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, account_name)
            )
        ''')
        # 3. 交易流水表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                日期 DATETIME,
                操作类型 TEXT,
                标的 TEXT,
                "数量(股)" REAL,
                "成交单价(¥)" REAL,
                "实际结算总金额(¥)" REAL,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        ''')
        conn.commit()

# --- 用户管理接口 ---
def verify_user(username, password):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        return cursor.fetchone() is not None

def register_user(username, password):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"

def update_password(username, old_pwd, new_pwd):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=? AND password=?", (new_pwd, username, old_pwd))
        conn.commit()
        return cursor.rowcount > 0

# --- 账户管理接口 ---
def get_user_id(username):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        return res[0] if res else None

def get_user_accounts(username):
    user_id = get_user_id(username)
    if not user_id: return []
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_name, last_accessed FROM accounts WHERE user_id=? ORDER BY last_accessed DESC", (user_id,))
        return [{"name": row[0], "last_accessed": row[1]} for row in cursor.fetchall()]

def create_account(username, account_name):
    user_id = get_user_id(username)
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO accounts (user_id, account_name, last_accessed) VALUES (?, ?, ?)", (user_id, account_name, now_str))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def update_account_access(username, account_name):
    user_id = get_user_id(username)
    with get_conn() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE accounts SET last_accessed=? WHERE user_id=? AND account_name=?", (now_str, user_id, account_name))
        conn.commit()

# --- 交易流水读写接口 ---
def get_account_id(username, account_name):
    user_id = get_user_id(username)
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE user_id=? AND account_name=?", (user_id, account_name))
        res = cursor.fetchone()
        return res[0] if res else None

def get_trades(username, account_name):
    acc_id = get_account_id(username, account_name)
    if not acc_id:
        return pd.DataFrame(columns=['日期', '操作类型', '标的', '数量(股)', '成交单价(¥)', '实际结算总金额(¥)'])
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT 日期, 操作类型, 标的, \"数量(股)\", \"成交单价(¥)\", \"实际结算总金额(¥)\" FROM trades WHERE account_id=?", conn, params=(acc_id,))
        if not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
        return df

def save_trades(username, account_name, df):
    """覆盖保存指定账户的流水表（适配 Streamlit 的 data_editor）"""
    acc_id = get_account_id(username, account_name)
    if not acc_id: return
    
    # 准备写入数据库的数据，追加 account_id
    df_to_save = df.copy()
    df_to_save['account_id'] = acc_id
    
    with get_conn() as conn:
        cursor = conn.cursor()
        # 清空该账户旧数据，使用全量覆盖的方式确保和前端 editor 完全同步
        cursor.execute("DELETE FROM trades WHERE account_id=?", (acc_id,))
        if not df_to_save.empty:
            # --- 💡 SQLite 终极格式转化防御 (隔离前端对象) ---
            sql_df = df_to_save.copy()
            
            # 智能嗅探所有疑似日期的列，强行洗成纯文本字符串！
            for col in sql_df.columns:
                if 'date' in str(col).lower() or '日期' in str(col):
                    sql_df[col] = pd.to_datetime(sql_df[col]).dt.strftime('%Y-%m-%d')
                    
            # 用洗干净的字符串副本去存数据库，绝不报错
            sql_df.to_sql('trades', conn, if_exists='append', index=False)

def delete_account(username, account_name):
    """安全删除账户及其所有关联的交易流水"""
    user_id = get_user_id(username)
    acc_id = get_account_id(username, account_name)
    if not acc_id: 
        return False
        
    with get_conn() as conn:
        cursor = conn.cursor()
        # 1. 必须先删除子表中的交易流水（防止外键约束报错/数据孤岛）
        cursor.execute("DELETE FROM trades WHERE account_id=?", (acc_id,))
        # 2. 删除主表中的账户
        cursor.execute("DELETE FROM accounts WHERE id=?", (acc_id,))
        conn.commit()
    return True

# ==========================================
# 投顾总结与寄语存储引擎 (支持按期归档与删除)
# ==========================================
import json
import os

COMMENTARY_FILE = "commentaries.json"

def get_all_commentaries(username, acc_name):
    """获取该账户下所有已存的寄语字典"""
    if not os.path.exists(COMMENTARY_FILE): return {}
    with open(COMMENTARY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    prefix = f"{username}_{acc_name}_"
    # 返回剔除前缀后的真实报告名称作为 key
    return {k[len(prefix):]: v for k, v in data.items() if k.startswith(prefix)}

def get_commentary(username, acc_name, report_name):
    """获取特定一期的投顾寄语"""
    if not os.path.exists(COMMENTARY_FILE): return ""
    with open(COMMENTARY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(f"{username}_{acc_name}_{report_name}", "")
    
def save_commentary(username, acc_name, report_name, text):
    """保存或更新特定一期的寄语"""
    data = {}
    if os.path.exists(COMMENTARY_FILE):
        with open(COMMENTARY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    data[f"{username}_{acc_name}_{report_name}"] = text
    with open(COMMENTARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def delete_commentary(username, acc_name, report_name):
    """彻底删除特定一期的寄语"""
    if not os.path.exists(COMMENTARY_FILE): return
    with open(COMMENTARY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    key = f"{username}_{acc_name}_{report_name}"
    if key in data:
        del data[key]
        with open(COMMENTARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)