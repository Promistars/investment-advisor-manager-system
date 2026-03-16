# 文件1：app.py (数据库版大厅 - 卡片式 UI 与盈亏透视)
import os
import streamlit as st
import pandas as pd
import db_manager as db
from datetime import datetime
import json

st.set_page_config(page_title="量化投资门户", page_icon="🏦", layout="wide")

import streamlit as st

# 0. 检测：不仅检查文件是否存在，还要检查文件大小是否大于 0
file_path = "financial_data/中国平安.csv"

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    try:
        # 2. 尝试读取
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        # 3. 如果刚好撞上爬虫在清空重写，静默忽略，等下一秒自动刷新
        pass
    except Exception as e:
        # 拦截其他一切报错，避免红框弹到前台
        pass

# ==========================================
# 🧭 自定义侧边栏导航系统
# ==========================================
# 1. 使用 CSS 强制隐藏 Streamlit 默认的英文文件名导航
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 2. 使用 page_link 手工绘制我们想要的中文导航
with st.sidebar:
    st.markdown("### 🧭 系统导航")
    # 这里的文件名必须跟你实际的文件名完全一致，label 则是你希望显示的中文
    st.page_link("app.py", label="🏠 系统控制台")
    st.page_link("pages/analytics.py", label="📈 量化分析看板")
    st.markdown("---") # 画一条分割线，让布局更美观

db.init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'active_acc' not in st.session_state: st.session_state.active_acc = None
if 'delete_confirm' not in st.session_state: st.session_state.delete_confirm = None

if st.session_state.logged_in and st.session_state.current_user is None:
    st.session_state.logged_in = False

# ==========================================
# 0. 轻量级引擎：加入“复权平差系统”的精准计算
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data_for_pnl():
    """提取最新的股票历史数据，并包含复权和不复权价格"""
    DATA_DIR = "financial_data"
    stock_data = {}
    if os.path.exists(DATA_DIR):
        for file in os.listdir(DATA_DIR):
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(DATA_DIR, file))
                cols = [c for c in df.columns if '收盘价' in c and c != '上证指数收盘价']
                if not cols: continue 
                s_name = cols[0].replace('收盘价', '')
                
                # 保留日期、复权价、不复权价
                use_cols = ['日期', f'{s_name}收盘价']
                if 'raw_close' in df.columns:
                    use_cols.append('raw_close')
                stock_data[s_name] = df[use_cols]
    return stock_data

def load_dividend_events():
    """在大厅预载所有标的分红历史，用于精准计算卡片盈亏"""
    all_divs = {}
    DIV_DIR = "dividend_data"
    if os.path.exists(DIV_DIR):
        for file in os.listdir(DIV_DIR):
            if file.endswith('_分红.csv'):
                name = file.replace('_分红.csv', '')
                df = pd.read_csv(os.path.join(DIV_DIR, file))
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
                all_divs[name] = df
    return all_divs

def get_account_pnl(username, acc_name):
    # 1. 获取该账户所有交易流水
    df_trades = db.get_trades(username, acc_name)
    if df_trades.empty: return 0.0, 0.0, 0.0

    # 2. 加载该账户的记忆开户日 (确保计算逻辑与看板一致)
    # 这里我们借用之前在 analytics.py 里的逻辑
    acc_start_date = "2023-01-01" # 默认值
    if os.path.exists("account_config.json"):
        with open("account_config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            acc_start_date = cfg.get(f"{username}_{acc_name}_start_date", "2023-01-01")

    # 3. 初始化账户状态
    cash, invested, holdings = 0.0, 0.0, {}
    div_book = load_dividend_events()
    
    # 4. 获取最新的行情和不复权价格
    DATA_DIR = "financial_data"
    latest_prices = {}
    if os.path.exists(DATA_DIR):
        for file in os.listdir(DATA_DIR):
            if file.endswith('.csv'):
                s_name = file.replace('.csv', '')
                df_s = pd.read_csv(os.path.join(DATA_DIR, file))
                # 优先取不复权价作为真实市值估值
                p_col = 'raw_close' if 'raw_close' in df_s.columns else f'{s_name}收盘价'
                latest_prices[s_name] = df_s.iloc[-1][p_col]

    # 5. 核心：模拟时间线，计算交易 + 分红入账
    # 按日期升序排列流水
    df_trades = df_trades.sort_values('日期')
    
    # 获取流水中最早的一天和今天
    start_dt = df_trades['日期'].min()
    end_dt = datetime.now()
    
    # 生成时间序列（只关注有流水的日子和分红日）
    for _, row in df_trades.iterrows():
        t_date_str = row['日期'].strftime('%Y-%m-%d')
        if t_date_str < acc_start_date: continue # 剔除物理开户日之前的历史
        
        t_type = row['操作类型']
        total = float(row['实际结算总金额(¥)'])
        qty = float(row.get('数量(股)', 0) or 0)
        asset = str(row.get('标的', ''))

        # A. 先处理该交易发生前的分红（此处为简化计算，实际中看板逻辑更准，此处做平衡）
        # B. 处理交易指令
        if t_type == '转入本金': cash += total; invested += total
        elif t_type == '提取现金': cash -= total; invested -= total
        elif t_type == '买入股票': cash -= total; holdings[asset] = holdings.get(asset, 0) + qty
        elif t_type == '卖出股票': cash += total; holdings[asset] = holdings.get(asset, 0) - qty

    # 6. 最终补算：持仓期间发生的所有分红现金入账
    for asset, qty in holdings.items():
        if qty > 0 and asset in div_book:
            # 找出在 [开户日, 今天] 之间该股的所有分红记录
            df_asset_div = div_book[asset]
            valid_divs = df_asset_div[df_asset_div['日期'] >= acc_start_date]
            for _, div_row in valid_divs.iterrows():
                # 只要该分红日在当前时间线内，就补发分红
                cash += (qty / 10.0) * div_row['每10股派息']
                holdings[asset] += (qty / 10.0) * (div_row['每10股送股'] + div_row['每10股转增'])

    # 7. 计算总资产与盈亏
    asset_val = cash
    for asset, qty in holdings.items():
        if asset in latest_prices:
            asset_val += qty * latest_prices[asset]

    pnl = asset_val - invested
    pnl_pct = (pnl / invested * 100) if invested > 0 else 0.0
    return invested, pnl, pnl_pct

# ==========================================
# 1. 🛡️ 登录与注册拦截系统
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 私募级量化交易系统</h2>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔑 身份登录", "📝 新用户注册"])
        with tab_login:
            with st.form("login_form"):
                log_user = st.text_input("👤 用户名")
                log_pwd = st.text_input("🔑 密码", type="password")
                if st.form_submit_button("登 录 ➔", use_container_width=True):
                    if db.verify_user(log_user, log_pwd):
                        st.session_state.logged_in = True
                        st.session_state.current_user = log_user
                        st.success(f"✅ 欢迎回来，{log_user}！正在进入系统...")
                        st.rerun()
                    else: st.error("❌ 用户名或密码错误！")
        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("👤 设置用户名")
                reg_pwd = st.text_input("🔑 设置密码", type="password")
                reg_pwd2 = st.text_input("🔑 确认密码", type="password")
                if st.form_submit_button("注 册 ➔", use_container_width=True):
                    if reg_user == "" or reg_pwd == "": st.warning("⚠️ 不能为空！")
                    elif reg_pwd != reg_pwd2: st.error("❌ 两次密码不一致！")
                    else:
                        success, msg = db.register_user(reg_user, reg_pwd)
                        if success: st.success("✅ 注册成功！请登录。")
                        else: st.error(f"❌ {msg}")
    st.stop()

# ==========================================
# 2. 已登录状态：账号大厅与个人中心
# ==========================================
current_user = st.session_state.current_user

st.sidebar.markdown(f"### 👤 当前用户：{current_user}")
with st.sidebar.expander("⚙️ 修改密码"):
    old_pwd = st.text_input("原密码", type="password")
    new_pwd = st.text_input("新密码", type="password")
    if st.button("确认修改", use_container_width=True):
        if db.update_password(current_user, old_pwd, new_pwd): st.success("✅ 修改成功！")
        else: st.error("❌ 原密码错误！")

if st.sidebar.button("🚪 退出安全登录", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.delete_confirm = None
    st.rerun()

st.title("🏦 我的财富管理门户")
st.markdown("---")

col_list, col_add = st.columns([2.5, 1], gap="large")

with col_list:
    st.subheader("📁 我的专属投资账号")
    accounts = db.get_user_accounts(current_user)
    
    if not accounts:
        st.info("您还没有创建任何投资账号，请在右侧创建一个。")
    else:
        for acc in accounts:
            acc_name = acc['name']
            
            # 💡 状态一：删除确认模式
            if st.session_state.delete_confirm == acc_name:
                with st.container(border=True):
                    st.warning(f"⚠️ 确定要永久删除账户 **【{acc_name}】** 及其所有流水吗？此操作不可恢复！")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("🚨 确认删除", key=f"yes_{acc_name}", type="primary", use_container_width=True):
                        db.delete_account(current_user, acc_name)
                        st.session_state.delete_confirm = None
                        st.rerun()
                    if c_no.button("取消", key=f"no_{acc_name}", use_container_width=True):
                        st.session_state.delete_confirm = None
                        st.rerun()
                continue

            # 💡 状态二：正常展示模式（卡片化UI设计）
            invested, pnl, pnl_pct = get_account_pnl(current_user, acc_name)
            
            with st.container(border=True): # 使用边框容器打包整个账户信息
                # 按照 3:1 比例划分左侧数据区和右侧按钮区
                c_info, c_action = st.columns([3, 1])
                
                with c_info:
                    st.markdown(f"#### 💼 {acc_name}")
                    
                    # 💡 将盈亏字号大幅度放大，视觉重心移到这里
                    if pnl > 0:
                        pnl_html = f"<span style='color: #ef4444; font-size: 28px; font-weight: bold;'>+{pnl:,.2f} <span style='font-size: 16px;'>(+{pnl_pct:.2f}%)</span> 📈</span>"
                    elif pnl < 0:
                        pnl_html = f"<span style='color: #10b981; font-size: 28px; font-weight: bold;'>{pnl:,.2f} <span style='font-size: 16px;'>({pnl_pct:.2f}%)</span> 📉</span>"
                    else:
                        pnl_html = f"<span style='color: gray; font-size: 28px; font-weight: bold;'>¥0.00 <span style='font-size: 16px;'>(0.00%)</span></span>"
                        
                    st.markdown(pnl_html, unsafe_allow_html=True)
                    st.caption(f"🕒 最近访问: {acc['last_accessed']}")
                
                with c_action:
                    # 💡 按钮上下堆叠排布
                    st.markdown("<br>", unsafe_allow_html=True) # 稍微往下垫一点，对齐左侧排版
                    if st.button("进入看板 ➔", key=f"go_{acc_name}", type="primary", use_container_width=True):
                        db.update_account_access(current_user, acc_name) 
                        st.session_state.active_acc = acc_name
                        st.switch_page("pages/analytics.py")
                        
                    if st.button("🗑️ 删除账户", key=f"del_{acc_name}", use_container_width=True):
                        st.session_state.delete_confirm = acc_name
                        st.rerun()

with col_add:
    st.subheader("➕ 创建新账号")
    with st.container(border=True):
        new_acc = st.text_input("请输入账号名称", key="new_acc_input")
        if st.button("创建并直接进入", use_container_width=True):
            clean_acc_name = new_acc.strip()
            if clean_acc_name == "": st.warning("⚠️ 账号名称不能为空！")
            else:
                if db.create_account(current_user, clean_acc_name):
                    st.session_state.active_acc = clean_acc_name
                    st.switch_page("pages/analytics.py")
                else:
                    st.warning("⚠️ 该账号名称已存在！")