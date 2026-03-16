# 文件2：pages/analytics.py (前后台隔离架构终极版)
import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import db_manager as db
import baostock as bs
import akshare as ak
import time
import streamlit as st
import json
import re
from streamlit_quill import st_quill
import streamlit.components.v1 as components

# ==========================================
# 0. 页面保护、鉴权与“客户专属链接”路由
# ==========================================
st.set_page_config(page_title="数据看板", page_icon="📊", layout="wide", initial_sidebar_state="auto")

# ==========================================
# 📱 移动端 (手机/Pad) 专属 UI 适配引擎
# ==========================================
st.markdown("""
    <style>
        /* 当屏幕宽度小于 768px 时（绝大多数手机的竖屏和部分横屏），自动激活以下规则 */
        @media (max-width: 768px) {
            /* 1. 极致拓宽视野：压缩 Streamlit 默认的巨大左右留白，把屏幕边缘还给数据 */
            .block-container {
                padding-top: 1.5rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-bottom: 1.5rem !important;
            }
            
            /* 2. 优雅的字体降级：缩小各级标题，防止在手机上出现丑陋的折行 */
            h1 { font-size: 1.5rem !important; }
            h2 { font-size: 1.3rem !important; }
            h3 { font-size: 1.1rem !important; }
            h4, h5 { font-size: 1rem !important; }
            
            /* 3. 指标卡片 (Metric) 瘦身：缩小大数字，让三个指标在手机上也能从容并排 */
            div[data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.8rem !important;
            }
            
            /* 4. 优化我们之前写的 JS 吸顶魔法：在手机上紧贴顶部，不浪费一寸垂直空间 */
            .client-sticky-header, .my-sticky-header {
                top: 0rem !important; 
                padding-top: 5px !important;
                padding-bottom: 5px !important;
            }
            
            /* 5. 隐藏图表右上角繁杂的工具栏（手机上根本点不到，还会挡住折线） */
            .modebar {
                display: none !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# 0.5 检测：不仅检查文件是否存在，还要检查文件大小是否大于 0
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
    st.page_link("pages/analytics.py", label="📈 投资分析看板")
    st.markdown("---") # 画一条分割线，让布局更美观

# 💡 核心机制：检查 URL 中是否携带专属访问参数
shared_user = st.query_params.get("user")
shared_acc = st.query_params.get("acc")
is_client_mode = (shared_user is not None) and (shared_acc is not None)

if is_client_mode:
    # 🌟 客户模式：隐身降权，强行隐藏左侧边栏和顶部导航栏
    st.markdown("""<style>[data-testid="collapsedControl"] {display: none;} [data-testid="stSidebar"] {display: none;} header {display: none;}</style>""", unsafe_allow_html=True)
    current_user = shared_user
    active_acc = shared_acc
    # 免密强制提取该账户数据
    st.session_state.trade_log = db.get_trades(current_user, active_acc)
    st.session_state.current_loaded_acc = active_acc
    st.title(f"📊 账户：{active_acc}")
else:
    # 👨‍💻 管理员模式：执行严格的登录校验
    if not st.session_state.get('logged_in', False): st.switch_page("app.py")
    if 'active_acc' not in st.session_state or st.session_state.active_acc is None: st.switch_page("app.py") 
    if 'violation_msg' not in st.session_state: st.session_state.violation_msg = ""
    
    current_user = st.session_state.current_user
    active_acc = st.session_state.active_acc
    
    if st.session_state.get('current_loaded_acc') != active_acc:
        st.session_state.trade_log = db.get_trades(current_user, active_acc)
        st.session_state.current_loaded_acc = active_acc

    # 👇 ================= 新增：JS引擎跨域吸顶魔法 (终极防弹版) ================= 👇
    col_title, col_back = st.columns([4, 1])
    
    # 1. 埋入隐形锚点，供 JS 追踪
    col_title.markdown(f"<div id='admin-sticky-anchor'></div><h2 style='margin: 0; padding: 0;'>📊 投顾控制台：{active_acc} <span style='font-size:18px; color:gray;'>(所属用户:{current_user})</span></h2>", unsafe_allow_html=True)
    
    if col_back.button("⬅️ 返回大厅", use_container_width=True):
        st.session_state.pop('trade_log', None)
        st.session_state.pop('current_loaded_acc', None)
        st.switch_page("app.py")

    # 2. 注入 JS 脚本，越过 Streamlit 的限制，直接操纵浏览器底层 DOM
    components.html(
        """
        <script>
        // 延时 0.5 秒执行，确保 Streamlit 网页已经完全加载完毕
        setTimeout(function() {
            try {
                const doc = window.parent.document;
                
                // A. 强行解除 Streamlit 最外层的滚动锁定（给悬浮腾出空间）
                const blockContainer = doc.querySelector('.block-container');
                if (blockContainer) {
                    blockContainer.style.overflow = 'visible';
                }

                // B. 顺藤摸瓜，找到我们的标题栏，给它贴上“悬浮许可”的标签
                const anchor = doc.getElementById('admin-sticky-anchor');
                if (anchor) {
                    const horizontalBlock = anchor.closest('div[data-testid="stHorizontalBlock"]');
                    if (horizontalBlock && horizontalBlock.parentElement) {
                        horizontalBlock.parentElement.classList.add('my-sticky-header');
                    }
                }

                // C. 将悬浮样式直接打入父网页的大脑 (<head>)，无视明暗主题切换！
                if (!doc.getElementById('sticky-style-inject')) {
                    const style = doc.createElement('style');
                    style.id = 'sticky-style-inject';
                    style.innerHTML = `
                        .my-sticky-header {
                            position: -webkit-sticky !important;
                            position: sticky !important;
                            top: 2.875rem !important; /* 刚好躲开系统菜单 */
                            z-index: 99999 !important; /* 图层置于最顶，盖住所有图表 */
                            background-color: var(--background-color, #ffffff) !important;
                            padding-top: 15px !important;
                            padding-bottom: 10px !important;
                            border-bottom: 1px solid rgba(128,128,128,0.2) !important;
                        }
                    `;
                    doc.head.appendChild(style);
                }
            } catch (e) {
                console.log("Sticky Header JS Error:", e);
            }
        }, 500);
        </script>
        """, 
        height=0, width=0
    )
    # 👆 ============================================================ 👆
# ==========================================
# 🧠 账户记忆模块：读取和保存开户基准日
# ==========================================
ACCOUNT_CONFIG_FILE = "account_config.json"

def get_acc_last_type(user, acc, default_type="转入本金"):
    if os.path.exists(ACCOUNT_CONFIG_FILE):
        try:
            with open(ACCOUNT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(f"{user}_{acc}_last_type", default_type)
        except: pass
    return default_type

def save_acc_last_type(user, acc, type_str):
    data = {}
    if os.path.exists(ACCOUNT_CONFIG_FILE):
        try:
            with open(ACCOUNT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
    data[f"{user}_{acc}_last_type"] = type_str
    with open(ACCOUNT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_acc_start_date(user, acc, default_date):
    if os.path.exists(ACCOUNT_CONFIG_FILE):
        try:
            with open(ACCOUNT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            d_str = data.get(f"{user}_{acc}_start_date")
            if d_str: return datetime.strptime(d_str, '%Y-%m-%d').date()
        except: pass
    return default_date

def save_acc_start_date(user, acc, date_obj):
    data = {}
    if os.path.exists(ACCOUNT_CONFIG_FILE):
        try:
            with open(ACCOUNT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
    data[f"{user}_{acc}_start_date"] = date_obj.strftime('%Y-%m-%d')
    with open(ACCOUNT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 1. 后台引擎：自动解析全局底层资产 (基准与个股解耦版)
# ==========================================
DATA_DIR = "financial_data"       # 📂 个股持仓数据目录
INDEX_DIR = "all_indices_data"    # 📂 全市场指数数据目录

# 🎯 终极接口：以后想换基准，只需在这里改名字！
BENCHMARK_NAME = "上证指数"

if not os.path.exists(DATA_DIR): st.error(f"❌ 找不到 '{DATA_DIR}' 文件夹！"); st.stop()
if not os.path.exists(INDEX_DIR): st.error(f"❌ 找不到 '{INDEX_DIR}' 文件夹！"); st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
if not csv_files: st.error("❌ 个股数据文件夹为空！"); st.stop()

# 解析个股中文名映射
stock_info = {}
for file in csv_files:
    df_temp = pd.read_csv(os.path.join(DATA_DIR, file), nrows=1)
    cols = [col for col in df_temp.columns if '收盘价' in col and col != f'{BENCHMARK_NAME}收盘价']
    if cols:
        stock_col = cols[0]
        stock_info[file] = stock_col.replace('收盘价', '')

stock_names = list(stock_info.values()) # 传给前端下拉菜单的股票池

@st.cache_data
def load_base_data(stock_files, benchmark):
    # 💡 核心修复：现在系统会去 INDEX_DIR (all_indices_data) 里面找基准文件了！
    index_path = os.path.join(INDEX_DIR, f"{benchmark}.csv")
    if not os.path.exists(index_path):
        st.error(f"❌ 找不到基准指数文件：{index_path}。请检查爬虫是否成功拉取。")
        st.stop()
        
    pdf = pd.read_csv(index_path)
    # 只抽取我们需要的数据（日期和基准收盘价）
    pdf = pdf[['日期', f'{benchmark}收盘价']]
    pdf['日期'] = pd.to_datetime(pdf['日期'])

    # 遍历 financial_data 中的个股，无缝拼接到基准主干上
    for file in stock_files:
        if file not in stock_info: continue
        df = pd.read_csv(os.path.join(DATA_DIR, file))
        
        # 统一时间格式
        df['日期'] = pd.to_datetime(df['日期'])
        s_name = stock_info[file]
        
        # 💡 核心平差系统数据层：准备合并的列（默认一定要有日期和复权收盘价）
        cols_to_merge = ['日期', f'{s_name}收盘价']
        
        # 如果爬虫文件里带有不复权价格，给它穿上中文马甲并一起提取
        if 'raw_close' in df.columns:
            df.rename(columns={'raw_close': f'{s_name}不复权收盘价'}, inplace=True)
            cols_to_merge.append(f'{s_name}不复权收盘价')
            
        # 精准合并到主表中
        pdf = pd.merge(pdf, df[cols_to_merge], on='日期', how='outer')
        
    return pdf.sort_values('日期').reset_index(drop=True).ffill().bfill()

def load_dividend_events(stock_names):
    """从 dividend_data 文件夹加载所有持仓标的分红历史"""
    all_divs = {}
    DIV_DIR = "dividend_data"
    for name in stock_names:
        path = os.path.join(DIV_DIR, f"{name}_分红.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            all_divs[name] = df
    return all_divs

portfolio_df = load_base_data(csv_files, BENCHMARK_NAME)
global_min_date = portfolio_df['日期'].min().date()
global_max_date = portfolio_df['日期'].max().date()

# ==========================================
# 2. 侧边栏：管理员专区 (定义账户生命周期与动态添股)
# ==========================================
if not is_client_mode:
    st.sidebar.header("⚙️ 内部管理员专区")
    st.sidebar.markdown("设定账户的**物理开户日**。系统将仅统计该日期及之后的资金和交易。")
    
    # 读取该账户的专属开户记忆
    saved_date = get_acc_start_date(current_user, active_acc, global_min_date)
    saved_date = max(global_min_date, min(saved_date, global_max_date)) # 确保在合法范围内
    
    account_start_date = st.sidebar.date_input("🗓️ 账户开户日 (基点)", value=saved_date, min_value=global_min_date, max_value=global_max_date)
    
    # 若被修改，立刻保存并触发系统重载
    if account_start_date != saved_date:
        save_acc_start_date(current_user, active_acc, account_start_date)
        st.rerun()   

    # 👇 ================= 新增：动态股票爬取引擎 ================= 👇
    st.sidebar.markdown("---")
    with st.sidebar.expander("➕ 动态添加新股票标的", expanded=False):
        st.markdown("<small>输入准确的A股中文简称，系统将自动寻址并抓取 2023 年至今的数据。</small>", unsafe_allow_html=True)
        new_stock_name = st.text_input("股票简称 (如: 招商银行)")
        
        if st.button("🚀 联网抓取并入库", use_container_width=True):
            if not new_stock_name:
                st.warning("名称不能为空")
            elif f"{new_stock_name}.csv" in os.listdir(DATA_DIR):
                st.info(f"【{new_stock_name}】的底层数据已存在，无需重复抓取。")
            else:
                with st.spinner(f"正在全市场匹配【{new_stock_name}】的代码..."):
                    try:
                        # 1. 调用 AkShare 获取A股全市场代码本
                        stock_info_df = ak.stock_info_a_code_name()
                        match = stock_info_df[stock_info_df['name'] == new_stock_name]
                        
                        if match.empty:
                            st.error(f"❌ 查无此股：未找到名为 '{new_stock_name}' 的A股公司，请检查是否有错别字。")
                        else:
                            # 2. 解析代码并转换为 BaoStock 格式
                            # 👇 核心修复：把 'symbol' 改成 'code'，并做个双重保险
                            if 'code' in match.columns:
                                raw_code = match.iloc[0]['code']
                            elif 'symbol' in match.columns:
                                raw_code = match.iloc[0]['symbol']
                            else:
                                raw_code = str(match.iloc[0].values[0]) # 兜底盲抓
                            # 2. 解析代码并转换为 BaoStock 格式
                            if raw_code.startswith('6'): bs_code = f"sh.{raw_code}"
                            elif raw_code.startswith('0') or raw_code.startswith('3'): bs_code = f"sz.{raw_code}"
                            elif raw_code.startswith('8') or raw_code.startswith('4') or raw_code.startswith('9'): bs_code = f"bj.{raw_code}"
                            else: bs_code = f"sh.{raw_code}" # 兜底
                            
                            st.info(f"✅ 匹配成功：代码为 {bs_code}。正在启动底层抓取引擎...")
                            
                            # 3. 启动 BaoStock 引擎实时拉取数据 (双路并行版)
                            bs.login()
                            
                            # 🎯 抓取 A 路：前复权数据 (用于系统分析和净值图表，平滑除权断层)
                            rs_adj = bs.query_history_k_data_plus(
                                bs_code,
                                "date,open,high,low,close,volume,amount,turn,pctChg,peTTM,pbMRQ",
                                start_date="2023-01-01", 
                                end_date=datetime.now().strftime("%Y-%m-%d"),
                                frequency="d",
                                adjustflag="2" # 前复权
                            )
                            
                            # 🎯 抓取 B 路：不复权数据 (专门提取真实收盘价，用于录入台单价)
                            rs_raw = bs.query_history_k_data_plus(
                                bs_code,
                                "date,close",
                                start_date="2023-01-01", 
                                end_date=datetime.now().strftime("%Y-%m-%d"),
                                frequency="d",
                                adjustflag="3" # 修正：BaoStock 中 3 才是真实不复权价
                            )
                            
                            data_adj = []
                            while (rs_adj.error_code == '0') & rs_adj.next():
                                data_adj.append(rs_adj.get_row_data())
                                
                            data_raw = []
                            while (rs_raw.error_code == '0') & rs_raw.next():
                                data_raw.append(rs_raw.get_row_data())
                            bs.logout()
                            
                            if not data_adj or not data_raw:
                                st.error(f"❌ 抓取失败：接口未返回 {new_stock_name} 的完整双路数据。")
                            else:
                                # 4. 数据融合与对齐
                                df_adj = pd.DataFrame(data_adj, columns=rs_adj.fields)
                                df_raw = pd.DataFrame(data_raw, columns=['date', 'raw_close'])
                                
                                # 将两路数据按日期合并
                                df_k = pd.merge(df_adj, df_raw, on='date', how='left')
                                
                                # 标准化重命名
                                df_k.rename(columns={
                                    'date': '日期', 
                                    'close': f'{new_stock_name}收盘价',
                                    'open': '开盘价', 'high': '最高价', 'low': '最低价',
                                    'volume': '成交量', 'amount': '成交额', 'turn': '换手率',
                                    'pctChg': '单日涨跌幅(%)', 'peTTM': '市盈率(PE)', 'pbMRQ': '市净率(PB)',
                                    'raw_close': f'{new_stock_name}不复权收盘价' # 👈 注入关键的真实单价列
                                }, inplace=True)
                                
                                # 日期转换与数值清洗
                                df_k['日期'] = pd.to_datetime(df_k['日期']).dt.strftime('%Y-%m-%d')
                                for col in df_k.columns:
                                    if col != '日期': 
                                        df_k[col] = pd.to_numeric(df_k[col], errors='coerce')
                                        
                                # 写入本地 CSV 仓库
                                file_path = os.path.join(DATA_DIR, f"{new_stock_name}.csv")
                                df_k.to_csv(file_path, index=False, encoding='utf-8-sig')
                                
                                # 👇 ================= 新增：将新标的永久写入后台爬虫配置 ================= 👇
                                config_path = "stock_config.json"
                                stock_dict = {}
                                if os.path.exists(config_path):
                                    with open(config_path, "r", encoding="utf-8") as f:
                                        stock_dict = json.load(f)
                                
                                # 将刚匹配到的 bs_code 和名字存入字典
                                stock_dict[bs_code] = new_stock_name
                                
                                with open(config_path, "w", encoding="utf-8") as f:
                                    json.dump(stock_dict, f, ensure_ascii=False, indent=4)
                                # 👆 ========================================================================= 👆
                                
                                # 👇 ====== 同步增加：动态抓取分红数据 ====== 👇
                                DIVIDEND_DIR = "dividend_data"
                                os.makedirs(DIVIDEND_DIR, exist_ok=True)
                                
                                try:
                                    pure_code = bs_code.split('.')[1]
                                    df_div = ak.stock_fhps_detail_em(symbol=pure_code)
                                    
                                    if not df_div.empty:
                                        date_col = next((c for c in df_div.columns if '除息' in c or '除权' in c), None)
                                        cash_col = next((c for c in df_div.columns if '派息' in c), None)
                                        send_col = next((c for c in df_div.columns if '送股' in c), None)
                                        trans_col = next((c for c in df_div.columns if '转增' in c), None)
                                        
                                        if date_col:
                                            df_div = df_div.dropna(subset=[date_col])
                                            std_div = pd.DataFrame()
                                            std_div['日期'] = pd.to_datetime(df_div[date_col]).dt.strftime('%Y-%m-%d')
                                            std_div['每10股派息'] = pd.to_numeric(df_div[cash_col], errors='coerce').fillna(0.0) if cash_col else 0.0
                                            std_div['每10股送股'] = pd.to_numeric(df_div[send_col], errors='coerce').fillna(0.0) if send_col else 0.0
                                            std_div['每10股转增'] = pd.to_numeric(df_div[trans_col], errors='coerce').fillna(0.0) if trans_col else 0.0
                                            
                                            std_div = std_div[std_div['日期'] >= '2023-01-01']
                                            if not std_div.empty:
                                                div_path = os.path.join(DIVIDEND_DIR, f"{new_stock_name}_分红.csv")
                                                std_div.to_csv(div_path, index=False, encoding='utf-8-sig')
                                except Exception as e:
                                    pass # 前台报错静默处理，以免影响客户体验
                                # 👆 ========================================= 👆

                                st.success(f"🎉 成功！【{new_stock_name}】数据已入库，并已加入后台自动更新序列！")
                                time.sleep(1.5)  # 稍微停顿让用户看清成功提示
                                
                                # 💡 强行清理缓存并重启页面，让新股票立刻出现在下拉菜单里！
                                st.cache_data.clear()
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f"❌ 系统异常: {e}")
    # 👆 ========================================================== 👆

else:
    # 客户模式下，默认从最早有数据的日期开始算起
    account_start_date = get_acc_start_date(current_user, active_acc, global_min_date)

# 💡 核心：生成“后台全量数据集”，剔除开户日之前的无效数据
admin_df = portfolio_df[portfolio_df['日期'].dt.date >= account_start_date].copy().reset_index(drop=True)
if admin_df.empty:
    st.error("❌ 选定日期之后没有可用的行情数据。")
    st.stop()


# ==========================================
# 3. 后台引擎：基于“开户日”运行撮合与回滚
# ==========================================
edited_trades = st.session_state.trade_log
txns_by_date = {}
for idx, row in edited_trades.dropna(subset=['日期', '操作类型', '实际结算总金额(¥)']).iterrows():
    dt = pd.to_datetime(row['日期']).date()
    if dt >= account_start_date: # 仅处理开户日之后的流水
        if dt not in txns_by_date: txns_by_date[dt] = []
        qty = float(row['数量(股)']) if pd.notnull(row['数量(股)']) else 0.0
        price = float(row['成交单价(¥)']) if pd.notnull(row['成交单价(¥)']) else 0.0
        txns_by_date[dt].append({'idx': idx, 'type': row['操作类型'], 'asset': str(row['标的']) if pd.notnull(row['标的']) else '', 'qty': qty, 'price': price, 'total': float(row['实际结算总金额(¥)'])})

dates = admin_df['日期'].tolist()
total_asset_series, cash_series, daily_fee_series, cum_fee_series, principal_series = [0.0]*len(dates), [0.0]*len(dates), [0.0]*len(dates), [0.0]*len(dates), [0.0]*len(dates)
holdings_series = {name: [0.0] * len(dates) for name in stock_names}
current_principal, current_cash, cumulative_fees = 0.0, 0.0, 0.0
current_holdings = {name: 0.0 for name in stock_names}

# 1. 预载分红账本
dividend_book = load_dividend_events(stock_names)

for i, row in admin_df.iterrows():
    date = row['日期'].date()
    daily_friction_cost = 0.0 
    
    # --- 💡 核心 A：分红/送股自动入账判定 ---
    for asset, qty in current_holdings.items():
        if qty > 0 and asset in dividend_book:
            # 检查今天是不是该股的分红日
            day_div = dividend_book[asset][dividend_book[asset]['日期'] == date]
            if not day_div.empty:
                div_info = day_div.iloc[0]
                # 1. 现金分红入账：(持仓/10) * 每10股派息
                cash_gain = (qty / 10.0) * div_info['每10股派息']
                if cash_gain > 0:
                    current_cash += cash_gain
                    # st.toast(f"💰 {date} {asset} 分红入账: ¥{cash_gain:,.2f}") # 可选提示
                
                # 2. 送转股入账：(持仓/10) * (送股+转增)
                new_shares = (qty / 10.0) * (div_info['每10股送股'] + div_info['每10股转增'])
                if new_shares > 0:
                    current_holdings[asset] += new_shares

    # --- 💡 核心 B：交易流水处理 (回归真实单价) ---
    for txn in txns_by_date.get(date, []):
        is_valid = True 
        if txn['type'] == '转入本金': 
            current_cash += txn['total']; current_principal += txn['total']
        elif txn['type'] == '提取现金': 
            if current_cash >= txn['total']: 
                current_cash -= txn['total']; current_principal -= txn['total']
            else: is_valid = False
        elif txn['type'] == '买入股票':
            if not txn['asset'] or current_cash < txn['total']: is_valid = False
            else:
                current_holdings[txn['asset']] += txn['qty'] 
                current_cash -= txn['total']
                diff = txn['total'] - (txn['qty'] * txn['price'])
                if diff > 0: daily_friction_cost += diff
        elif txn['type'] == '卖出股票':
            if not txn['asset'] or current_holdings.get(txn['asset'], 0) < txn['qty']: is_valid = False
            else:
                current_holdings[txn['asset']] -= txn['qty']
                current_cash += txn['total']
                diff = (txn['qty'] * txn['price']) - txn['total']
                if diff > 0: daily_friction_cost += diff
        # 👇 新增：管理费与结账重置逻辑
        elif txn['type'] == '提取管理费(内扣)':
            if current_cash >= txn['total']:
                current_cash -= txn['total']
                current_principal -= txn['total'] # 视为资金流出
            else: is_valid = False
        elif txn['type'] == '结账重置(外付)':
            pass # 外付不影响账户内资金，仅作为生成新一期水位线的物理标记

        if not is_valid:
            st.session_state.trade_log = st.session_state.trade_log.drop(txn['idx'])
            db.save_trades(current_user, active_acc, st.session_state.trade_log)
            st.rerun()
            
    # --- 💡 核心 C：总资产估值 (使用不复权真实市价) ---
    # 这样除权当天股价下跌，你的持仓市值减少，但现金刚好增加，总资产保持平稳
    total_market_val = 0.0
    for name in stock_names:
        price = row[f"{name}不复权收盘价"] if f"{name}不复权收盘价" in row else row[f"{name}收盘价"]
        total_market_val += current_holdings[name] * price
    
    total_asset_series[i] = current_cash + total_market_val
    cash_series[i] = current_cash; daily_fee_series[i] = daily_friction_cost; cumulative_fees += daily_friction_cost
    cum_fee_series[i] = cumulative_fees; principal_series[i] = current_principal 
    for name in stock_names: holdings_series[name][i] = current_holdings[name]

admin_df['总持仓市值'] = total_asset_series; admin_df['账户可用现金'] = cash_series
admin_df['当日产生税费'] = daily_fee_series; admin_df['累计税费'] = cum_fee_series
admin_df['累计税费'] = cum_fee_series
admin_df['累计净本金'] = principal_series 
for name in stock_names: admin_df[f'{name}_持仓'] = holdings_series[name]

admin_df['每日净流入'] = admin_df['累计净本金'].diff().fillna(admin_df['累计净本金'])
admin_df['前日总资产'] = admin_df['总持仓市值'].shift(1).fillna(0)
admin_df['单日成本基数'] = admin_df['前日总资产'] + admin_df['每日净流入'].clip(lower=0)
admin_df['单日盈亏'] = admin_df['总持仓市值'] - admin_df['前日总资产'] - admin_df['每日净流入']
admin_df['账户当日收益率'] = np.where(
    admin_df['单日成本基数'] > 0,
    (admin_df['单日盈亏'] / admin_df['单日成本基数']) * 100,
    0.0
)
admin_df['精确组合净值'] = (1.0 + admin_df['账户当日收益率'] / 100.0).cumprod()

# 👇 核心修复：把丢失的大盘单日收益率补回来！
admin_df['大盘当日收益率'] = admin_df[f'{BENCHMARK_NAME}收盘价'].pct_change().fillna(0) * 100

# 获取最新一天作为管理后台的状态快照
admin_latest = admin_df.iloc[-1]
snap_date_str = admin_latest['日期'].strftime('%Y-%m-%d')
snap_cash = admin_latest['账户可用现金']
snap_fees = admin_latest['累计税费']

# ==========================================
# 4. 后台 UI：交易台、底层雷达、持仓胶囊、对账单
# ==========================================
if not is_client_mode:
        
    st.markdown("### 👨‍💻 内部管理与操作台 (含持仓底牌)")
    
    col_input, col_radar = st.columns([1.5, 1], gap="large")


    with col_input:
        st.subheader(f"📝 交易录入台")
        if st.session_state.violation_msg:
            st.error(st.session_state.violation_msg, icon="🚫")
            if st.button("我知道了，确认回滚", type="primary"):
                st.session_state.violation_msg = "" 
                st.rerun() 
        else:
            with st.container():
                c1, c2 = st.columns(2)
                # 录入日期最低被限制为开户日
                t_date = c1.date_input("📅 操作日期", value=global_max_date, min_value=account_start_date, max_value=global_max_date)
                
                # 1. 定义选项列表
                type_options = ['转入本金', '买入股票', '卖出股票', '提取现金']
                # 2. 从记忆库读取上一次的操作类型
                last_type = get_acc_last_type(current_user, active_acc, "转入本金")
                # 3. 计算该类型在列表中的索引（index）
                try:
                    default_idx = type_options.index(last_type)
                except ValueError:
                    default_idx = 0
                # 4. 渲染选择框，并设定默认索引
                t_type = c2.selectbox("🔄 操作类型", type_options, index=default_idx)
                                
                if t_type in ['买入股票', '卖出股票']:
                    c3, c4, c5 = st.columns(3)

                    # --- 🎯 交易标的：智能排序逻辑 (适配 c3 布局) ---
                    all_stock_options = stock_names 

                    # 1. 提取最近操作过的标的顺序
                    if not st.session_state.trade_log.empty:
                        # 按日期倒序，取唯一的标的名
                        # 👇 终极防混排报错：利用 key 参数，在排序瞬间强制统一所有格式！
                        recent_assets = st.session_state.trade_log.sort_values('日期', ascending=False, key=pd.to_datetime)['标的'].unique().tolist()
                        
                        # 过滤与合并：最近操作的排前面 + 剩下的排后面
                        recent_assets = [a for a in recent_assets if a in all_stock_options]
                        never_traded = [a for a in all_stock_options if a not in recent_assets]
                        sorted_assets = recent_assets + never_traded
                    else:
                        sorted_assets = all_stock_options

                    # 2. 正式渲染到 c3 列
                    t_asset = c3.selectbox("🎯 交易标的", sorted_assets)
                    suggested_price = 10.00 
                    # 💡 强制让录入台寻找“不复权”价格，这样才会和你的券商APP对上
                    # --- 🎯 强制校准建议单价逻辑 ---
                    if t_asset:
                        # 获取该资产的所有历史数据
                        past_data = admin_df[admin_df['日期'].dt.date <= t_date]
                        
                        if not past_data.empty:
                            # 重点：定义我们要寻找的列名优先级
                            # 1. 优先找我们专门存的“不复权”列
                            raw_col = f"{t_asset}不复权收盘价"
                            # 2. 备选：如果有些老数据只有“收盘价”
                            normal_col = f"{t_asset}收盘价"
                            
                            # 强制判定
                            if raw_col in past_data.columns:
                                suggested_price = float(past_data.iloc[-1][raw_col])
                            elif normal_col in past_data.columns:
                                suggested_price = float(past_data.iloc[-1][normal_col])
                            else:
                                suggested_price = 0.0
                                
                            # 💡 终极调试：如果显示的还是 190 多，请取消下面这行的注释
                            # st.write(f"⚠️ 调试信息：当前读取列为 {raw_col if raw_col in past_data.columns else normal_col}，值为 {suggested_price}")
                    t_qty = c4.number_input("📦 数量(股)", min_value=1, step=100, value=100)
                    t_price = c5.number_input("🏷️ 单价(¥)", min_value=0.01, value=suggested_price, format="%.2f")
                    t_total = st.number_input("💰 结算总额(¥) [含税费]", min_value=0.01, value=float(t_qty * t_price), format="%.2f")
                else:
                    t_asset, t_qty, t_price = '', 0.0, 0.0
                    t_total = st.number_input("💰 划转总额(¥)", min_value=0.01, value=100000.0, format="%.2f", step=10000.0)

                if st.button("✅ 确认并录入指令", use_container_width=True, type="primary"):
                    if t_total <= 0: st.error("⚠️ 录入失败：结算总额必须大于 0！")
                    else:
                        save_acc_last_type(current_user, active_acc, t_type)
                        new_row = pd.DataFrame({'日期': [pd.to_datetime(t_date)], '操作类型': [t_type], '标的': [t_asset if t_asset != '' else None], '数量(股)': [t_qty if t_qty > 0 else None], '成交单价(¥)': [t_price if t_price > 0 else None], '实际结算总金额(¥)': [t_total]})
                        st.session_state.trade_log = pd.concat([st.session_state.trade_log, new_row], ignore_index=True)
                        db.save_trades(current_user, active_acc, st.session_state.trade_log)
                        st.rerun()

    # 持仓胶囊 (属于后台管理，向客户隐藏底牌)
    st.markdown("---")
    st.subheader(f"📊 底层资金与持仓结构 (截至 **{snap_date_str}**)")
    bar_placeholder = st.empty()
    pie_labels, pie_values, pie_qtys = ['可用现金'], [max(snap_cash, 0)], [0.0] 
    for asset in stock_names:
        qty = admin_latest[f'{asset}_持仓']
        if qty > 0:
            pie_labels.append(asset); pie_values.append(qty * admin_latest[f'{asset}收盘价']); pie_qtys.append(qty)

    valid_items = [(i, label, val, pie_qtys[i]) for i, (label, val) in enumerate(zip(pie_labels, pie_values)) if val > 0]
    total_val = sum(v for _, _, v, _ in valid_items)

    if total_val > 0:
        colors = ['#34D399', '#60A5FA', '#818CF8', '#A78BFA', '#F472B6', '#FBBF24', '#22D3EE']
        css_styles = """<style>.cbt{position:relative;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold;cursor:pointer;transition:filter 0.2s;}.cbt:hover{filter:brightness(1.1);}.cbt .tt{visibility:hidden;background-color:rgba(30,41,59,0.95);color:#fff;text-align:center;border-radius:8px;padding:10px;position:absolute;z-index:9999;bottom:130%;left:50%;transform:translateX(-50%);font-size:13px;font-weight:normal;opacity:0;transition:opacity 0.2s, bottom 0.2s;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);pointer-events:none;line-height:1.6;white-space:nowrap;}.cbt .tt::after{content:"";position:absolute;top:100%;left:50%;margin-left:-6px;border-width:6px;border-style:solid;border-color:rgba(30,41,59,0.95) transparent transparent transparent;}.cbt:hover .tt{visibility:visible;opacity:1;bottom:140%;}</style>"""
        html_legend = '<div style="display:flex;justify-content:center;gap:20px;margin-bottom:16px;">'
        html_bar = '<div style="width:100%;height:38px;display:flex;box-shadow:0 2px 4px rgba(0,0,0,0.1);border-radius:19px;">'
        
        for idx, (orig_i, label, val, qty) in enumerate(valid_items):
            pct = (val / total_val) * 100
            color = colors[orig_i % len(colors)]
            html_legend += f'<div style="display:flex;align-items:center;font-size:13px;"><div style="width:12px;height:12px;background-color:{color};border-radius:3px;margin-right:6px;"></div>{label}</div>'
            b_rad = ""
            if idx == 0: b_rad += "border-top-left-radius:19px; border-bottom-left-radius:19px; "
            if idx == len(valid_items) - 1: b_rad += "border-top-right-radius:19px; border-bottom-right-radius:19px; "
            b_right = "border-right:1.5px solid white;" if idx != len(valid_items) - 1 else ""
            tooltip_content = f'金额: <b style="font-size:14px;">¥{val:,.2f}</b><br>占比: {pct:.1f}%' if label == '可用现金' else f'当前估值: <b style="font-size:14px;">¥{val:,.2f}</b><br>持有数量: <b>{qty:,.0f} 股</b><br>占比: {pct:.1f}%'
            html_bar += f'<div class="cbt" style="width:{pct}%;background-color:{color};{b_right}{b_rad}">{pct:.1f}%<span class="tt"><b style="font-size:14px;color:{color};">{label}</b><br>{tooltip_content}</span></div>'
            
        html_legend += '</div>'; html_bar += '</div>'
        bar_placeholder.markdown(f'<div translate="no" class="notranslate">{(css_styles + html_legend + html_bar).replace(chr(10), "")}</div>', unsafe_allow_html=True)
    else: bar_placeholder.info("📦 账户资产为空。")


    # 👇 提前定义全局嗅探器（给图表和结算模块共用）
    log_df = st.session_state.trade_log
    def sniff_col(df, keywords, default_name):
        if df.empty: return default_name
        for col in df.columns:
            for kw in keywords:
                if kw.lower() in str(col).lower():
                    return col
        return default_name
    # ==========================================
    # 💡 新增：管理员专属带标注走势图
    # ==========================================
    st.markdown("### 📊 账户历史操作全景图")
    admin_fig = go.Figure()
    
    # 1. 画出资产总净值底线
    admin_fig.add_trace(go.Scatter(x=admin_df['日期'], y=admin_df['总持仓市值'], mode='lines', name='总资产', line=dict(color='#3b82f6', width=2)))
    
    # 2. 把流水日记里的操作挂载到图表上
    log_df = st.session_state.trade_log.copy()
    
    # 图表同样需要兼容中文表头
    c_type_chart = sniff_col(log_df, ['操作类型', 'type', '类型'], 'type')
    c_date_chart = sniff_col(log_df, ['操作日期', 'date', '日期', '时间'], 'date')
    c_tot_chart  = sniff_col(log_df, ['结算总金额', 'total', '总额', '金额'], 'total')
    
    if not log_df.empty and c_type_chart in log_df.columns and c_date_chart in log_df.columns:
        log_df['date_ts'] = pd.to_datetime(log_df[c_date_chart])
        
        # ⚠️ 注意：下面的 for 循环里，把 t_data = log_df[log_df['type'] == t_type]
        # 改成 
        # 以及 hovertemplate 里面的 t_data['total'] 改成 t_data[c_tot_chart]

        # 定义不同操作的颜色和图标
        marker_map = {
            '买入股票': dict(color='red', symbol='triangle-up', name='买入', size=10),
            '卖出股票': dict(color='green', symbol='triangle-down', name='卖出', size=10),
            '转入本金': dict(color='gold', symbol='star', name='注资', size=12),
            '提取现金': dict(color='grey', symbol='x', name='赎回', size=10),
            '提取管理费(内扣)': dict(color='purple', symbol='diamond', name='内扣结账', size=14),
            '结账重置(外付)': dict(color='purple', symbol='diamond-open', name='外付结账', size=14)
        }
        
        for t_type, m_style in marker_map.items():
            t_data = log_df[log_df[c_type_chart] == t_type]
            if not t_data.empty:
                # 匹配图表上的 Y 值
                y_vals = []
                for d in t_data['date_ts']:
                    match = admin_df[admin_df['日期'] == d]['总持仓市值']
                    y_vals.append(match.iloc[0] if not match.empty else np.nan)
                
                admin_fig.add_trace(go.Scatter(
                    x=t_data['date_ts'], y=y_vals,
                    mode='markers', name=m_style['name'],
                    marker=dict(color=m_style['color'], symbol=m_style['symbol'], size=m_style['size'], line=dict(width=1, color='white')),
                    hovertemplate=f"<b>{m_style['name']}</b><br>日期: %{{x}}<br>金额/数量: " + t_data[c_tot_chart].astype(str) + "<extra></extra>"
                ))

    admin_fig.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.02, x=0))
    st.plotly_chart(admin_fig, use_container_width=True)


    # ==========================================
    # 💡 新增模块：智能业绩报酬与高水位线结算引擎
    # ==========================================
    st.markdown("---")
    st.markdown("### 💰 业绩报酬与结算周期管理")
    
    log_df = st.session_state.trade_log
    
    c_type = sniff_col(log_df, ['操作类型', 'type', '类型'], 'type')
    c_date = sniff_col(log_df, ['操作日期', 'date', '日期', '时间'], 'date')
    c_tot  = sniff_col(log_df, ['结算总金额', 'total', '总额', '金额'], 'total')
    c_prc  = sniff_col(log_df, ['单价', 'price'], 'price')
    c_ast  = sniff_col(log_df, ['交易标的', 'asset', '标的', '代码'], 'asset')
    c_qty  = sniff_col(log_df, ['数量', 'qty', '股'], 'qty')
    
    # 👇 核心升级 1：建立绝对时间轴，彻底抛弃物理行号
    log_df_sorted = log_df.copy()
    if not log_df_sorted.empty and c_date in log_df_sorted.columns:
        log_df_sorted['__date_val'] = pd.to_datetime(log_df_sorted[c_date]).dt.date
    
    if not log_df_sorted.empty and c_type in log_df_sorted.columns:
        billing_txns = log_df_sorted[log_df_sorted[c_type].isin(['提取管理费(内扣)', '结账重置(外付)'])]
    else:
        billing_txns = pd.DataFrame()
        
    if not billing_txns.empty:
        # 按时间排序，找到时间线上真正的最后一次结账
        billing_txns = billing_txns.sort_values(by='__date_val')
        last_billing_row = billing_txns.iloc[-1]
        last_watermark_date = last_billing_row['__date_val']
        base_watermark = last_billing_row[c_prc]
        
        # 严格提取时间在上次结账【之后】的操作
        subsequent_txns = log_df_sorted[log_df_sorted['__date_val'] > last_watermark_date]
    else:
        last_watermark_date = account_start_date
        base_watermark = 0.0
        subsequent_txns = log_df_sorted if not log_df_sorted.empty else pd.DataFrame()
        
    recent_net_inflow = 0.0
    if not subsequent_txns.empty and c_type in subsequent_txns.columns and c_tot in subsequent_txns.columns:
        # 加入强转数字护甲
        inflows = pd.to_numeric(subsequent_txns[subsequent_txns[c_type] == '转入本金'][c_tot], errors='coerce').fillna(0).sum()
        outflows = pd.to_numeric(subsequent_txns[subsequent_txns[c_type] == '提取现金'][c_tot], errors='coerce').fillna(0).sum()
        recent_net_inflow = inflows - outflows
        
    adjusted_watermark = base_watermark + recent_net_inflow
    if adjusted_watermark <= 0: adjusted_watermark = 1.0 
    
    current_asset_now = admin_latest['总持仓市值']
    period_profit = current_asset_now - adjusted_watermark
    
    # --- 👇 核心升级：双轨制目标设定 UI ---
    st.markdown(" ") # 稍微空一行，排版更好看
    target_mode = st.radio("🎯 设定结账目标方式", ["按约定收益率 (%)", "手动指定目标总资产 (¥)"], horizontal=True)
    
    c_fee1, c_fee2, c_fee3, c_fee4 = st.columns(4)
    fee_ratio = c_fee2.number_input("🤝 利润分成比例 (%)", value=st.session_state.get('fee_ratio', 20.0), step=1.0)
    st.session_state['fee_ratio'] = fee_ratio
    
    # 💡 魔法切换器：根据你的选择，动态改变第一个输入框的功能！
    if target_mode == "按约定收益率 (%)":
        target_pct = c_fee1.number_input("🎯 结账触发收益率 (%)", value=st.session_state.get('fee_target', 20.0), step=1.0)
        st.session_state['fee_target'] = target_pct
        # 收益率模式：系统帮你算出目标金额
        target_asset = adjusted_watermark * (1.0 + target_pct / 100.0)
    else:
        default_target = st.session_state.get('fee_target_asset', float(adjusted_watermark * 1.2))
        # 手动模式：你直接输入目标金额
        target_asset = c_fee1.number_input("🎯 目标总资产 (¥)", value=default_target, step=1000.0)
        st.session_state['fee_target_asset'] = target_asset
        # 系统反推算出一个理论收益率，用于后面的展示
        target_pct = ((target_asset / adjusted_watermark) - 1.0) * 100 if adjusted_watermark > 0 else 0.0

    c_fee3.metric("🚩 触发结账目标总资产", f"¥{target_asset:,.2f}", f"基数(期初+追加): ¥{adjusted_watermark:,.2f}", delta_color="off")
    
    if current_asset_now >= target_asset:
        c_fee4.metric("🌟 当前账户总资产 (已达标)", f"¥{current_asset_now:,.2f}", f"+ ¥{current_asset_now - target_asset:,.2f} (溢出目标)")
    else:
        c_fee4.metric("📈 当前账户总资产 (未达标)", f"¥{current_asset_now:,.2f}", f"- ¥{target_asset - current_asset_now:,.2f} (距结账还差)")
    
    # 强制时间重排保存机制 (保持之前的内外双轨不变)
    def add_and_save_billing(d, t, p, tot):
        new_log = pd.DataFrame([{c_date: d, c_type: t, c_ast: '管理费', c_qty: 1, c_prc: p, c_tot: tot}])
        merged = pd.concat([log_df, new_log], ignore_index=True)
        merged[c_date] = pd.to_datetime(merged[c_date]).dt.date
        merged = merged.sort_values(by=c_date).reset_index(drop=True)
        st.session_state.trade_log = merged
        save_df = merged.copy()
        save_df[c_date] = pd.to_datetime(save_df[c_date]).dt.strftime('%Y-%m-%d')
        db.save_trades(current_user, active_acc, save_df)
        st.rerun()

    # 3. 达标判定逻辑
    if current_asset_now >= target_asset:
        agreed_profit = target_asset - adjusted_watermark
        fee_amount = agreed_profit * (fee_ratio / 100.0)
        target_watermark = target_asset
        extra_profit = current_asset_now - target_asset 
        
        st.success(f"🎉 **收益已达标！** 当前绝对利润 ¥{period_profit:,.2f}。\n**[系统已执行截断结算]** 目标利润 (¥{agreed_profit:,.2f}) 按 {fee_ratio}% 计提，应收：**¥{fee_amount:,.2f}**。\n*(溢出的 ¥{extra_profit:,.2f} 利润不收提成，自动结转为新一期的起步利润！)*")
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("💸 立即内扣管理费 (溢出利润滚入下期)", use_container_width=True):
                add_and_save_billing(pd.Timestamp(global_max_date).date(), '提取管理费(内扣)', target_watermark - fee_amount, fee_amount)
        with b2:
            if st.button("🤝 立即外付管理费 (溢出利润滚入下期)", use_container_width=True):
                add_and_save_billing(pd.Timestamp(global_max_date).date(), '结账重置(外付)', target_watermark, fee_amount)
    elif period_profit > 0:
        st.info(f"⏳ 账户最新状态正在盈利中，距离自动触发结账还差 ¥{target_asset - current_asset_now:,.2f}")
    else:
        st.info("📉 账户最新状态处于动态水位线之下，暂无结账利润。")

    # 👇 时光机同步兼容双轨制
    with st.expander("🛠️ 强制补录历史结账 (防止利润回撤错失结算点)", expanded=False):
        st.markdown("<span style='font-size:13px; color:gray;'>即使历史最高峰溢出了约定目标，系统也会智能截断，只收取达标部分的费用，将多余利润无损继承到新周期。</span>", unsafe_allow_html=True)
        
        m_col1, m_col2 = st.columns(2)
        manual_date = m_col1.date_input("📅 选择历史巅峰达标日", value=pd.Timestamp(global_max_date).date(), min_value=last_watermark_date, max_value=pd.Timestamp(global_max_date).date())
        
        hist_admin = admin_df[admin_df['日期'].dt.date <= manual_date]
        if not hist_admin.empty:
            hist_asset = hist_admin.iloc[-1]['总持仓市值']
            
            hist_net_inflow = 0.0
            if not subsequent_txns.empty and c_type in subsequent_txns.columns:
                hist_txns = subsequent_txns[subsequent_txns['__date_val'] <= manual_date]
                h_inflows = pd.to_numeric(hist_txns[hist_txns[c_type] == '转入本金'][c_tot], errors='coerce').fillna(0).sum()
                h_outflows = pd.to_numeric(hist_txns[hist_txns[c_type] == '提取现金'][c_tot], errors='coerce').fillna(0).sum()
                hist_net_inflow = h_inflows - h_outflows
            
            hist_watermark = base_watermark + hist_net_inflow
            if hist_watermark <= 0: hist_watermark = 1.0
            
            # 💡 时光机也会根据你上面选的模式，自动决定是用百分比算，还是直接用你敲定的目标金额！
            if target_mode == "按约定收益率 (%)":
                hist_target_asset = hist_watermark * (1.0 + target_pct / 100.0)
            else:
                hist_target_asset = target_asset
            
            if hist_asset >= hist_target_asset:
                agreed_hist_profit = hist_target_asset - hist_watermark
                hist_fee = agreed_hist_profit * (fee_ratio / 100.0)
                target_hist_watermark = hist_target_asset
                
                m_col2.success(f"✅ 该日达标！(截取约定利润结算)\n目标利润: ¥{agreed_hist_profit:,.2f} | 截断应收: ¥{hist_fee:,.2f}")
            else:
                hist_profit_actual = hist_asset - hist_watermark
                hist_fee = hist_profit_actual * (fee_ratio / 100.0) if hist_profit_actual > 0 else 0.0
                target_hist_watermark = hist_asset 
                m_col2.warning(f"⚠️ 该日未达标 (差 ¥{hist_target_asset - hist_asset:,.2f})\n将按全额利润强制结账: ¥{hist_fee:,.2f}")
            
            manual_fee = st.number_input("💰 确认实际提取金额 (支持手动抹零微调)", value=float(max(0, hist_fee)), step=100.0)
            
            mb1, mb2 = st.columns(2)
            with mb1:
                if st.button(f"💸 按 {manual_date} 补录内扣", use_container_width=True, key="m_in"):
                    add_and_save_billing(manual_date, '提取管理费(内扣)', target_hist_watermark - manual_fee, manual_fee)
            with mb2:
                if st.button(f"🤝 按 {manual_date} 补录外付", use_container_width=True, key="m_out"):
                    add_and_save_billing(manual_date, '结账重置(外付)', target_hist_watermark, manual_fee)
    
    # ==========================================
    # 👇 新增：专属历史结算记录表 (倒序展示)
    # ==========================================
    st.markdown("#### 📜 历史结算明细")
    
    if not billing_txns.empty:
        # 拷贝一份历史记录，按时间倒序排列 (最新的结账在最上面)
        billing_history = billing_txns.sort_values(by='__date_val', ascending=False).copy()
        
        # 提取并重命名我们需要展示的核心列，让财务人员看得更顺眼
        display_df = pd.DataFrame()
        display_df['结算日期'] = billing_history[c_date]
        display_df['结算方式'] = billing_history[c_type]
        display_df['结账后新起点(水位线)'] = billing_history[c_prc].apply(lambda x: f"¥ {x:,.2f}")
        display_df['提取管理费金额'] = billing_history[c_tot].apply(lambda x: f"¥ {x:,.2f}")
        
        # 使用 Streamlit 原生表格优美地展示出来
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📂 当前账户暂无任何历史结算/提取管理费记录。")


    with col_radar:
        st.subheader("🎯 账户实时监控雷达")
        st.markdown(f"*(截至全量最新：**{snap_date_str}** 收盘)*")
        st.metric("💵 可用现金储备", f"¥{snap_cash:,.2f}")
        st.metric("📉 累计交易损耗 (含税费)", f"¥{snap_fees:,.2f}", f"-{snap_fees:,.2f}", delta_color="inverse")

    st.markdown("---")
    st.markdown(f"##### 📋 内部历史指令账本 (管理员维护区)")
    with st.expander("展开查看历史指令与对账单", expanded=False):

        # 💡 终极 PyArrow 渲染防爆锁：确保交给组件前，所有的日期列绝对纯净！
        if not st.session_state.trade_log.empty:
            for col in st.session_state.trade_log.columns:
                if '日期' in str(col) or 'date' in str(col).lower():
                    # 强行统一为 Python 原生的 date 对象
                    st.session_state.trade_log[col] = pd.to_datetime(st.session_state.trade_log[col]).dt.date

        new_edited_trades = st.data_editor(
            st.session_state.trade_log,
            num_rows="dynamic", hide_index=True,    
            column_config={
                "日期": st.column_config.DateColumn("操作日期", required=True),
                "操作类型": st.column_config.SelectboxColumn("操作类型", options=['转入本金', '提取现金', '买入股票', '卖出股票'], required=True),
                "标的": st.column_config.SelectboxColumn("交易标的", options=stock_names, required=False), 
                "数量(股)": st.column_config.NumberColumn("数量(股)", min_value=1, step=100),
                "成交单价(¥)": st.column_config.NumberColumn("单价(¥)", min_value=0.01, format="%.2f"),
                "实际结算总金额(¥)": st.column_config.NumberColumn("结算总金额(¥)", min_value=0.01, required=True, format="%.2f")
            },
            use_container_width=True, height=300, key=f"editor_{current_user}_{active_acc}" 
        )
        if not new_edited_trades.equals(st.session_state.trade_log):
            st.session_state.trade_log = new_edited_trades
            db.save_trades(current_user, active_acc, new_edited_trades)
            st.rerun()

           

        st.markdown("##### 📋 全量对账单 (倒序展示)")
        
        # 👇 1. 扩宽视野：找出历史上“曾经持有过”或“现在正持有”的所有标的
        ever_held_stocks = [asset for asset in stock_names if admin_df[f'{asset}_持仓'].max() > 0]
        
        # 2. 拼接基础展示列
        display_cols = ['日期', '总持仓市值', '累计净本金', '账户可用现金', '精确组合净值', f'{BENCHMARK_NAME}收盘价']
        show_df = admin_df.copy()
        
        # 👇 3. 核心魔法：动态处理历史股价遮罩
        for asset in ever_held_stocks:
            # 判断条件：当天持仓 > 0，或者前一天持仓 > 0 (为了精准保留全部清仓卖出那一天的价格)
            is_holding = (show_df[f'{asset}_持仓'] > 0) | (show_df[f'{asset}_持仓'].shift(1) > 0)
            
            # 动态改写：将没有持仓的日子的价格设为 NaN (前端会自动渲染为干净的空白)
            show_df[f'{asset}收盘价'] = np.where(is_holding, show_df[f'{asset}收盘价'], np.nan)
            display_cols.append(f'{asset}收盘价')
            
        # 4. 提取展示切片并优化格式
        show_df = show_df[display_cols]
        show_df['日期'] = show_df['日期'].dt.strftime('%Y-%m-%d')
        show_df = show_df.iloc[::-1] # 倒序排列，最新日期置顶
        
        st.dataframe(show_df, hide_index=True, use_container_width=True)

    # 👇 新增：后台投顾分析撰写面板
    # 👇 升级版：后台投顾分析撰写与管理面板
    st.markdown("### 📝 投顾研报寄语管理")
    
    # 自动生成当前对应的三个报告期名称，用于绑定
    _today = datetime.now().date()
    _last_month = _today.replace(day=1) - timedelta(days=1)
    rep_month = f"{_last_month.strftime('%Y年%m月')}-月报"
    
    _pq = ((_today.month - 1) // 3 + 1) - 1
    _pq_yr = _today.year if _pq > 0 else _today.year - 1
    _pq = _pq if _pq > 0 else 4
    rep_quarter = f"{_pq_yr}年Q{_pq}-季报"
    rep_year = f"{_today.year - 1}年-年报"
    
    # 💡 将撰写区和归档库统统装进这一个带边框的容器里
    with st.container(border=True):
        
        # 💡 核心武器：终极魔法翻译器（自带跨平台兼容与最高权限重写）
        # 💡 核心武器：终极魔法翻译器（注入 CSS Class，无视 Streamlit 底层字体拦截）
        def apply_magic_format(raw_text):
            if not raw_text: return ""
            
            # 1. 翻译链接
            res = re.sub(
                r'\[([^\]]+)\]\((http[^)]+)\)', 
                r'<a href="\2" target="_blank" style="color: #3b82f6; text-decoration: underline;">\1</a>', 
                raw_text
            )
            
            # 2. 翻译字体（改为贴上 Class 身份证）
            font_class_map = {
                "楷体": "magic-font-kaiti",
                "宋体": "magic-font-songti",
                "黑体": "magic-font-heiti",
                "微软雅黑": "magic-font-yahei",
                "Times": "magic-font-times"
            }
            
            def _replacer(m):
                text, font_name = m.group(1), m.group(2)
                cls_name = font_class_map.get(font_name, "")
                if cls_name:
                    return f'<span class="{cls_name}">{text}</span>'
                return m.group(0) # 如果用户字体名打错了，就原样返回
            
            res = re.sub(r'\[([^\]]+)\]\(font:([^)]+)\)', _replacer, res)
            
            # 3. 强行注入 CSS 全局样式表（DOMPurify 无法洗掉这部分规则）
            css_inject = """
            <style>
            .magic-font-kaiti { font-family: 'KaiTi', 'STKaiti', '楷体', serif !important; }
            .magic-font-songti { font-family: 'SimSun', 'STSong', '宋体', serif !important; }
            .magic-font-heiti { font-family: 'SimHei', 'STHeiti', '黑体', sans-serif !important; }
            .magic-font-yahei { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important; }
            .magic-font-times { font-family: 'Times New Roman', Times, serif !important; }
            </style>
            """
            
            return css_inject + res


        # 1. 撰写区 (原生零延迟工具栏 + 双列实时预览)
        rep_type = st.selectbox("🎯 选择要撰写/更新的报告期：", [rep_month, rep_quarter, rep_year])
        
        # 👇 核心修复 1：把当前账户名(active_acc)焊死在钥匙上，彻底消灭切换账户时的残影！
        quill_key = f"quill_content_{active_acc}_{rep_type}"
        if quill_key not in st.session_state:
            st.session_state[quill_key] = db.get_commentary(current_user, active_acc, rep_type)

        st.caption("📝 左侧使用工具栏进行基础排版（纯前端零延迟），遇到缺少的功能（如链接）直接输入 Markdown 语法，右侧实时预览。")

        # 定义满血版原生工具栏（精准剔除 link 和 font）
        custom_toolbar = [
            ['bold', 'italic', 'underline', 'strike'],
            [{'script': 'sub'}, {'script': 'super'}],
            [{'background': []}, {'color': []}],
            [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}, {'align': []}],
            [{'header': 1}, {'header': 2}, {'header': [1, 2, 3, 4, 5, 6, False]}],
            [{'size': ['small', False, 'large', 'huge']}],
            ['formula', 'blockquote', 'code-block', 'clean', 'image'] 
        ]

        
        c_edit, c_preview = st.columns(2)
        
        with c_edit:
            st.markdown("✍️ **富文本编辑区**")
            current_content = st_quill(
                value=st.session_state[quill_key], 
                toolbar=custom_toolbar, 
                html=True, 
                # 👇 核心修复 2：给 Quill 组件的物理 ID 也贴上账户标签
                key=f"quill_comp_{active_acc}_{rep_type}"
            )
            if current_content != st.session_state[quill_key]:
                st.session_state[quill_key] = current_content
                
        with c_preview:
            st.markdown("👁️ **实时排版预览**")
            with st.container(border=True):
                raw_content = st.session_state.get(quill_key, "")
                if raw_content and raw_content.strip():
                    # 💡 预览时调用统一翻译器
                    st.markdown(apply_magic_format(raw_content), unsafe_allow_html=True)
                else:
                    st.info("👈 左侧输入内容，此处将实时展示最终给客户看到的排版效果...")

        with st.expander("💡 进阶：如何插入超链接与特定中英文字体？（点击查看语法）", expanded=False):
            st.markdown("""
            请直接在左侧像打字一样输入以下极简语法，系统会自动将其转化为高级排版：
            
            **🔗 插入超链接**
            * 语法：`[点击查看财报](http://www.baidu.com)`
            
            **🔤 插入经典字体** (格式为 `[文字](font:字体名称)`)
            * **楷体**：`[这里是楷体文字](font:楷体)`
            * **宋体**：`[这里是宋体文字](font:宋体)`
            * **黑体**：`[这里是黑体文字](font:黑体)`
            * **微软雅黑**：`[这里是雅黑文字](font:微软雅黑)`
            * **Times 英文**：`[Times Roman Text](font:Times)`
            
            *(注：请尽量**手动输入**语法，若直接复制上方代码导致带上灰底，可选中文字后点击工具栏最右侧的 `Tx` 按钮清除格式)*
            """)

        if st.button("💾 保存/更新投顾寄语", type="primary"):
            # 💡 保存前调用统一翻译器，完美 HTML 入库
            final_content = apply_magic_format(st.session_state.get(quill_key, ""))
            db.save_commentary(current_user, active_acc, rep_type, final_content)
            st.success(f"✅ 【{rep_type}】寄语已保存！")
            st.rerun()

        # 💡 分割线，让上下区域更分明
        st.markdown("---") 

        # 2. 已写寄语显示栏与删除功能（全部缩进，收进上方的 container 内）
        saved_comms = db.get_all_commentaries(current_user, active_acc)
        if saved_comms:
            st.markdown("##### 🗂️ 已归档寄语库")
            for r_name, txt in saved_comms.items():
                # 名字直接使用：账号名 - 时间 - 报告种类
                with st.expander(f"📄 {active_acc} - {r_name}"):
                    st.markdown(txt)
                    st.markdown("---")
                    del_key = f"del_{r_name}"
                    confirm_key = f"confirm_{r_name}"
                    
                    if st.button("🗑️ 删除此份报告寄语", key=del_key):
                        st.session_state[confirm_key] = True
                        st.rerun()
                        
                    # 弹窗效果：二次确认拦截
                    if st.session_state.get(confirm_key, False):
                        st.warning("⚠️ 确定要删除吗？删除后客户将无法看到此报告的寄语。")
                        c_yes, c_no = st.columns([1, 1])
                        if c_yes.button("🚨 我已知晓，彻底删除", key=f"do_{confirm_key}", type="primary", use_container_width=True):
                            db.delete_commentary(current_user, active_acc, r_name)
                            st.session_state[confirm_key] = False
                            st.rerun()
                        if c_no.button("取消", key=f"cancel_{confirm_key}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()

    with st.expander("🔗 获取发送给客户的专属汇报链接", expanded=False):
        st.info("💡 请选择客户打开链接时默认看到的报告维度，然后一键复制下方完整链接。")
        
        # 💡 核心配置：在这里填入你刚才在 Ngrok 认领的固定域名（注意不要结尾的斜杠）
        BASE_URL = "https://unintimate-armida-insensibly.ngrok-free.dev/analytics" 
        
        link_view_mode = st.radio("设置链接的默认视角：", ["月报视图", "季报视图", "年报视图"], horizontal=True)
        view_code = "month"
        if link_view_mode == "季报视图": view_code = "quarter"
        elif link_view_mode == "年报视图": view_code = "year"
        
        # 智能拼接完整公网链接
        share_url = f"{BASE_URL}/?user={current_user}&acc={active_acc}&view={view_code}" 
        
        # 直接展示完整链接，方便一键复制
        st.code(share_url, language="text")
        # 附赠一个小功能：直接生成可点击的超链接，方便你自己做测试
        st.markdown(f"👉 **[点击这里，模拟客户在公网直接打开]({share_url})**")

# ==============================================================================
# ==============================================================================
# 5. 前台 UI：客户展示大屏 (物理隔离持仓底牌，统一多维分析)
# ==============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)

# 👇 关键0：在这里埋下一个隐形的“滚动触发器”，作为物理碰撞的检测线
st.markdown("<div id='client-scroll-trigger' style='height: 1px; width: 100%; margin-bottom: -1px;'></div>", unsafe_allow_html=True)

# 💡 视觉优化：使用 1:4:1 的绝对对称列，确保中间的标题完美居中全局，右侧按钮紧贴屏幕边缘
c_empty, c_title, c_print = st.columns([1, 4, 1])

with c_title:
    # 👇 关键1：在这里埋下客户专属的隐形锚点
    st.markdown("<div id='client-sticky-anchor'></div><h2 style='text-align: center; color: #1E293B; margin: 0;'>🌐 客户汇报与展示大屏</h2>", unsafe_allow_html=True)

with c_print:
    components.html(
        """
        <div style="display: flex; justify-content: flex-end; align-items: center; padding-top: 3px;">
            <button onclick="window.parent.print()" style="padding: 8px 16px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-family: sans-serif; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                🖨️ 导出 PDF
            </button>
        </div>
        """, 
        height=45
    )

# 👇 ================= 新增：客户大屏 JS 碰撞推挤魔法 ================= 👇
components.html(
    """
    <script>
    setTimeout(function() {
        try {
            const doc = window.parent.document;
            
            // 1. 基础悬浮设置
            const blockContainer = doc.querySelector('.block-container');
            if (blockContainer) blockContainer.style.overflow = 'visible';

            const anchor = doc.getElementById('client-sticky-anchor');
            if (anchor) {
                const horizontalBlock = anchor.closest('div[data-testid="stHorizontalBlock"]');
                if (horizontalBlock && horizontalBlock.parentElement) {
                    horizontalBlock.parentElement.classList.add('client-sticky-header');
                }
            }

            if (!doc.getElementById('client-sticky-style-inject')) {
                const style = doc.createElement('style');
                style.id = 'client-sticky-style-inject';
                style.innerHTML = `
                    .client-sticky-header {
                        position: -webkit-sticky !important;
                        position: sticky !important;
                        top: 2.875rem !important; 
                        z-index: 99998 !important; 
                        background-color: var(--background-color, #ffffff) !important;
                        padding-top: 15px !important;
                        padding-bottom: 10px !important;
                        margin-top: -15px !important;
                        border-bottom: 1px solid rgba(128,128,128,0.2) !important;
                    }
                `;
                doc.head.appendChild(style);
            }

            // --- 🎯 核心特效：实时碰撞检测与向上推挤 ---
            doc.addEventListener('scroll', function() {
                // 找到我们刚才埋下的隐形触发器 和 上方的投顾控制台
                const trigger = doc.getElementById('client-scroll-trigger');
                const adminHeader = doc.querySelector('.my-sticky-header');
                
                if (trigger && adminHeader) {
                    const triggerRect = trigger.getBoundingClientRect();
                    const adminHeight = adminHeader.offsetHeight || 60; // 获取控制台高度
                    const stickyThreshold = 46; // 悬浮基准线 (2.875rem ≈ 46px)
                    
                    // 阶段A：当客户大屏撞上投顾控制台时，按像素等比例将其向上推走
                    if (triggerRect.top <= stickyThreshold + adminHeight && triggerRect.top > stickyThreshold) {
                        const pushAmount = (stickyThreshold + adminHeight) - triggerRect.top;
                        adminHeader.style.transform = 'translateY(-' + pushAmount + 'px)';
                        adminHeader.style.visibility = 'visible';
                    } 
                    // 阶段B：客户大屏完全就位，投顾控制台被彻底顶出屏幕
                    else if (triggerRect.top <= stickyThreshold) {
                        adminHeader.style.transform = 'translateY(-' + adminHeight + 'px)';
                        adminHeader.style.visibility = 'hidden'; // 隐藏防误触
                    } 
                    // 阶段C：往回滚，投顾控制台复位
                    else {
                        adminHeader.style.transform = 'translateY(0px)';
                        adminHeader.style.visibility = 'visible';
                    }
                }
            }, true); // useCapture=true 确保精准捕获滚动轴

        } catch (e) {
            console.log("Client Sticky Header JS Error:", e);
        }
    }, 500);
    </script>
    """, 
    height=0, width=0
)
# 👆 ============================================================ 👆

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

st.subheader("📊 核心指标与业绩分析曲线")

# 1. 自动推算各个自然周期的起止时间点
today = datetime.now().date()

# 上月
last_day_prev_month = today.replace(day=1) - timedelta(days=1)
first_day_prev_month = last_day_prev_month.replace(day=1)

# 上季度
current_quarter = (today.month - 1) // 3 + 1
prev_quarter = current_quarter - 1
prev_q_year = today.year if prev_quarter > 0 else today.year - 1
prev_quarter = prev_quarter if prev_quarter > 0 else 4
first_day_prev_q = datetime(prev_q_year, 3 * prev_quarter - 2, 1).date()
last_day_prev_q = datetime(prev_q_year, 3 * prev_quarter, calendar.monthrange(prev_q_year, 3 * prev_quarter)[1]).date()

# 上一年
first_day_prev_year = datetime(today.year - 1, 1, 1).date()
last_day_prev_year = datetime(today.year - 1, 12, 31).date()

# 💡 核心安全机制：数据封锁。判定当前角色允许查看的最大日期
# 客户只能看到上个月底；管理员可以看到全局全量数据
client_max_date = min(global_max_date, last_day_prev_month)
max_selectable_date = client_max_date if is_client_mode else global_max_date

# 2. 交互式维度选择器 (根据账户生命周期动态过滤)
account_lifespan = (today - account_start_date).days

# 💡 核心增强：按运行天数逐步解锁报告维度
available_options = []
if account_lifespan >= 30:
    available_options.append(f"月度报告 (上月: {first_day_prev_month.strftime('%m')}月)")
if account_lifespan >= 90:
    available_options.append(f"季度报告 (上季: Q{prev_quarter})")
    available_options.append("自定义区间") # 满一季度解锁自定义
if account_lifespan >= 365:
    available_options.append(f"年度报告 (去年: {today.year - 1}年)")

# 如果账户不满 30 天，没有任何选项可以看，直接拦截并提示
if not available_options:
    st.info(f"🐣 账户处于起步期（已运行 {account_lifespan} 天），暂无完整月度报表。")
    st.warning("📌 提示：该区间内可用的底层行情数据不足（少于2天），无法生成有效测算曲线。")
    st.stop()

# 解析管理员通过 URL 传过来的默认视图参数
url_view = st.query_params.get("view", "month")

# 智能匹配默认选项（兜底为当前可用的第一个选项）
default_opt = available_options[0]
if url_view == "quarter" and f"季度报告 (上季: Q{prev_quarter})" in available_options:
    default_opt = f"季度报告 (上季: Q{prev_quarter})"
elif url_view == "year" and f"年度报告 (去年: {today.year - 1}年)" in available_options:
    default_opt = f"年度报告 (去年: {today.year - 1}年)"

radio_key = f"view_mode_{active_acc}"
if radio_key not in st.session_state or st.session_state[radio_key] not in available_options:
    st.session_state[radio_key] = default_opt

view_mode = st.radio(
    "⏱️ 请选择业绩分析维度", 
    available_options, 
    horizontal=True,
    key=radio_key
)

st.markdown("<br>", unsafe_allow_html=True)

if "月度报告" in view_mode:
    perf_start, perf_end = first_day_prev_month, last_day_prev_month
elif "季度报告" in view_mode:
    perf_start, perf_end = first_day_prev_q, last_day_prev_q
elif "年度报告" in view_mode:
    perf_start, perf_end = first_day_prev_year, last_day_prev_year
else:
    c_date, c_space = st.columns([1, 2])
    # 💡 限制客户的日历选择器：最大不能超过上个月末 (max_selectable_date)
    safe_start_date = min(account_start_date, max_selectable_date)
    date_range = c_date.date_input("📅 请选择自定义展示区间", [safe_start_date, max_selectable_date], min_value=safe_start_date, max_value=max_selectable_date)
    if len(date_range) != 2: st.stop()
    perf_start, perf_end = date_range

# 兜底保险：不管你怎么乱选，结束日期强行被物理截断在最大允许日期以内
if perf_end > max_selectable_date:
    perf_end = max_selectable_date
    perf_start = min(perf_start, perf_end)

# 4. 提取对应的展示切片
client_df = admin_df[(admin_df['日期'].dt.date >= perf_start) & (admin_df['日期'].dt.date <= perf_end)].copy()
if len(client_df) < 2:
    st.warning("📌 提示：该区间内可用的底层行情数据不足，无法生成有效测算曲线。")
    st.stop()

# 5. 核心测算逻辑 (复用顶级测算引擎)
c_first = client_df.iloc[0]
c_latest = client_df.iloc[-1]
client_start_idx = client_df.index[0] 

if client_start_idx == 0:
    prev_asset, prev_principal, prev_index = 0.0, 0.0, admin_df[f'{BENCHMARK_NAME}收盘价'].iloc[0]
else:
    prev_asset = admin_df.loc[client_start_idx - 1, '总持仓市值']
    prev_principal = admin_df.loc[client_start_idx - 1, '累计净本金']
    prev_index = admin_df.loc[client_start_idx - 1, f'{BENCHMARK_NAME}收盘价']

period_net_inflow = c_latest['累计净本金'] - prev_principal
period_pnl = c_latest['总持仓市值'] - prev_asset - period_net_inflow
period_cost_base = prev_asset + max(0, period_net_inflow)
if period_cost_base <= 0: period_cost_base = max(client_df['累计净本金'].max(), 1.0)

portfolio_change = (period_pnl / period_cost_base) * 100
index_change = (c_latest[f'{BENCHMARK_NAME}收盘价'] / prev_index - 1.0) * 100
alpha = portfolio_change - index_change

# 💡 优化：提取真实的有效数据起止日期（防止开户日晚于自然周期的起点）
actual_start_str = c_first['日期'].strftime('%Y-%m-%d')
actual_end_str = c_latest['日期'].strftime('%Y-%m-%d')

c_info1, c_info2 = st.columns([1, 1])
c_info1.markdown(f"*(实际有效数据区间：**{actual_start_str}** 至 **{actual_end_str}**)*")

# 👇 完美补回被遗漏的“区间净流入”指标！
c_info2.markdown(f"<div style='text-align: right;'><span style='color:gray;font-size:14px;'>⚖️ 该区间净充值/流入本金: <b>¥{period_net_inflow:,.2f}</b></span></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("💰 期末真实总资产", f"¥{c_latest['总持仓市值']:,.2f}", f"{portfolio_change:+.2f}% (区间回报)", delta_color="inverse", 
            help="该区间最后一日的账户总资产估值。区间回报 = (期末资产 - 期初资产 - 期间净转入) / 成本基数")
col2.metric("📈 " + BENCHMARK_NAME + " 同期表现", f"{c_latest[f'{BENCHMARK_NAME}收盘价']:,.2f}", f"{index_change:+.2f}% (基准涨跌)", delta_color="inverse", 
            help="同一时间区间内，" + BENCHMARK_NAME + "指数的累计涨跌幅，作为大盘基准参考。")
col3.metric("🔥 区间超额收益", f"{alpha:+.2f}%", f"{alpha:+.2f}% (相较大盘)", delta_color="inverse", 
            help="账户区间回报率减去大盘基准涨跌幅，正数说明跑赢大盘，负数说明跑输大盘。")
st.markdown("<br>", unsafe_allow_html=True)

client_df['历史最高净值'] = client_df['精确组合净值'].cummax()
client_df['回撤幅度'] = (client_df['精确组合净值'] - client_df['历史最高净值']) / client_df['历史最高净值']
max_drawdown = client_df['回撤幅度'].min() * 100 

delta_days = max(1, (c_latest['日期'] - c_first['日期']).days)
annual_return = portfolio_change * (365.0 / delta_days)

daily_returns = client_df['账户当日收益率'] / 100.0  
daily_volatility = daily_returns.std()
annual_volatility = daily_volatility * np.sqrt(252) * 100 if pd.notnull(daily_volatility) else 0.0

daily_rf = 0.02 / 252
excess_returns = daily_returns - daily_rf
sharpe_ratio = (excess_returns.mean() / daily_volatility) * np.sqrt(252) if daily_volatility > 0 else 0.0

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("📉 区间最大回撤", f"{max_drawdown:.2f}%", f"{max_drawdown:.2f}% (极值跌幅)", delta_color="inverse", 
              help="该区间内，账户净值从最高点回落到最低点的最大跌幅，用于衡量面临的极端风险。")

# 💡 只有在非“月度报告”的情况下才显示年化收益率
if "月度报告" not in view_mode:
    col_r2.metric("🚀 年化收益率", f"{annual_return:.2f}%", f"{annual_return:+.2f}% (预期折算)", delta_color="inverse", 
                  help="将当前区间的绝对收益率，按实际日历天数线性折算为一整年的预期收益率。")
else:
    # 月度报告中，col_r2 留空占位
    col_r2.empty() 

if sharpe_ratio > 1:
    col_r3.metric("⚖️ 夏普比率 (Sharpe)", f"{sharpe_ratio:.2f}", 
                  help="衡量承担每单位风险所获得的超额回报。数值越高，代表经风险调整后的性价比越好（通常 >1 算优秀）。")
st.markdown("<br>", unsafe_allow_html=True)

# 6. 客户图表渲染
client_df['区间内累计净流入'] = client_df['累计净本金'] - prev_principal
client_df['区间内累计净盈亏'] = client_df['总持仓市值'] - prev_asset - client_df['区间内累计净流入']
client_df['区间成本基数'] = prev_asset + client_df['区间内累计净流入'].clip(lower=0)

client_df['账户累计收益率'] = np.where(client_df['区间成本基数'] > 0, (client_df['区间内累计净盈亏'] / client_df['区间成本基数']) * 100, 0.0)
client_df['大盘累计收益率'] = (client_df[f'{BENCHMARK_NAME}收盘价'] / prev_index - 1.0) * 100

client_df['账户当日_str'] = client_df['账户当日收益率'].apply(lambda x: f"{x:+.2f}%")
client_df['账户累计_str'] = client_df['账户累计收益率'].apply(lambda x: f"{x:+.2f}%")
client_df['大盘当日_str'] = client_df['大盘当日收益率'].apply(lambda x: f"{x:+.2f}%")
client_df['大盘累计_str'] = client_df['大盘累计收益率'].apply(lambda x: f"{x:+.2f}%")
custom_data_matrix = client_df[['账户当日_str', '账户累计_str', '大盘当日_str', '大盘累计_str']].values

tab1, tab2 = st.tabs(["📈 累计收益率走势图 (区间动态汇报)", "📊 真实资产走势图 (仅展示总量)"])

with tab1:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=client_df['日期'], y=client_df['账户累计收益率'], customdata=custom_data_matrix, mode='lines', name='本投资组合', line=dict(color='#ef4444', width=3), hovertemplate="<b>组合回报</b><br>单日波动: %{customdata[0]}<br>累计回报: %{customdata[1]}<extra></extra>"))
    fig2.add_trace(go.Scatter(x=client_df['日期'], y=client_df['大盘累计收益率'], customdata=custom_data_matrix, mode='lines', name='沪深300 (大盘基准)', line=dict(color='#3b82f6', width=2), hovertemplate="<b>大盘基准</b><br>单日波动: %{customdata[2]}<br>累计涨幅: %{customdata[3]}<extra></extra>"))
    fig2.update_layout(hovermode="x unified", yaxis_title="累计收益率 (%)", yaxis=dict(ticksuffix="%"), margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=client_df['日期'], y=client_df['总持仓市值'], mode='lines', name='客户总资产', line=dict(color='#ef4444', width=3), hovertemplate="总资产: ¥%{y:,.2f}<extra></extra>"))
    fig1.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    st.plotly_chart(fig1, use_container_width=True)

# ==========================================
# 8. 前台展示模块（根据客户当前选择的维度，精准匹配对应月份的寄语）
# ==========================================
if "月度报告" in view_mode: current_rep_name = f"{first_day_prev_month.strftime('%Y年%m月')}-月报"
elif "季度报告" in view_mode: current_rep_name = f"{prev_q_year}年Q{prev_quarter}-季报"
elif "年度报告" in view_mode: current_rep_name = f"{today.year - 1}年-年报"
else: current_rep_name = ""

# 💡 核心修复：把 current_rep_name 作为第 3 个参数传进去！自定义区间则不展示任何固定寄语。
client_commentary = db.get_commentary(current_user, active_acc, current_rep_name) if current_rep_name else ""

if client_commentary and client_commentary.strip() != "":
    st.markdown("<hr style='margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.subheader(f"💡 投顾分析与决策展望 ({current_rep_name})")
    with st.container(border=True):
        # 👇 核心修复：增加 unsafe_allow_html=True，让富文本的排版生效
        st.markdown(client_commentary, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

