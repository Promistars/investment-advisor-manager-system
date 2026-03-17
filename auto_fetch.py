import os
import pandas as pd
from datetime import datetime, timedelta
import baostock as bs
import akshare as ak
import time
import json # 👈 确保在最上方导入 json 模块

# ==========================================
# 🎯 核心配置：动态股票池读取引擎
# ==========================================
CONFIG_FILE = "stock_config.json"
DATA_DIR = "financial_data"        # 存放你的核心个股和上证指数
FUNDA_DIR = "fundamental_data"     # 存放财务基本面数据
REALTIME_DIR = "realtime_data"     # 存放实时行情快照
INDEX_DIR = "all_indices_data"     # 存放全市场数百个指数的独立历史文件
DIVIDEND_DIR = "dividend_data"     # 👈 [新增] 存放历史分红派息事件库

# 记得把新建的文件夹也加到检查列表里
for d in [DATA_DIR, FUNDA_DIR, REALTIME_DIR, INDEX_DIR, DIVIDEND_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

DEFAULT_STOCKS = {
    'sh.601318': '中国平安',
    'sh.600519': '贵州茅台',
    'sh.601658': '邮储银行',
    'sh.600036': '招商银行',
}
# 自动生成或读取配置文件
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        TARGET_STOCKS = json.load(f)
else:
    TARGET_STOCKS = DEFAULT_STOCKS
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(TARGET_STOCKS, f, ensure_ascii=False, indent=4)

TX_STOCKS = {k.replace('.', ''): v for k, v in TARGET_STOCKS.items()}

def get_latest_trading_date():
    """🕵️ 智能探针：向 BaoStock 询问系统里最新可用的交易日是哪天（自动跳过周末/节假日）"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    # 拿上证指数最近14天的数据试探
    rs = bs.query_history_k_data_plus("sh.000001", "date", start_date=start_date, end_date=end_date, frequency="d")
    dates = []
    while (rs.error_code == '0') & rs.next():
        dates.append(rs.get_row_data()[0])
    return dates[-1] if dates else end_date

def fetch_data_now():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 启动智能增量抓取引擎...")

    # ==========================================
    # 🌟 模块 0: 获取新浪指数花名册
    # ==========================================
    print("\n⏳ [阶段 1] 正在获取全市场指数清单...")
    try:
        df_indices = ak.stock_zh_index_spot_sina()
        total_indices = len(df_indices)
        print(f"✅ 成功发现 {total_indices} 个指数。")
    except Exception as e:
        print(f"❌ 获取指数列表失败: {e}")
        df_indices = pd.DataFrame()

    lg = bs.login()
    if lg.error_code == '0':
        
        # 👇 核心升级：获取全网最新交易日作为“校验锚点”
        latest_trade_date = get_latest_trading_date()
        print(f"📌 系统当前最新有效交易日探测为: 【{latest_trade_date}】")
        
        if not df_indices.empty:
            print(f"\n⏳ [阶段 2] 开始智能排查与抓取 {total_indices} 个指数 (2023年至今)...")
            start_date = "2023-01-01"
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            success_count = 0
            skip_count = 0
            
            for i, row in df_indices.iterrows():
                code = row['代码']
                name = str(row['名称'])
                
                if str(code).startswith('sh') or str(code).startswith('sz'):
                    bs_code = f"{code[:2]}.{code[2:]}"
                else:
                    continue

                safe_name = name.replace('/', '_').replace('\\', '_').replace('*', '').replace('?', '')
                file_path = os.path.join(INDEX_DIR, f"{safe_name}.csv")
                
                # 👇================ 核心：智能跳过逻辑 ================👇
                if os.path.exists(file_path):
                    try:
                        # 仅读取最后几行校验日期，极速完成
                        df_exist = pd.read_csv(file_path)
                        if not df_exist.empty and '日期' in df_exist.columns:
                            last_date_in_file = str(df_exist['日期'].iloc[-1])
                            if last_date_in_file >= latest_trade_date:
                                skip_count += 1
                                # 为了控制台干净，不打印每条跳过信息
                                continue
                    except Exception:
                        pass # 如果文件损坏，直接往下走重新爬取
                # 👆====================================================👆

                # 走到这里的，都是【没爬过的】或者【数据落后的】，开始老老实实爬取
                if (success_count + 1) % 10 == 0:
                    print(f"  🔄 发现缺失/落后数据，正在抓取: {name} ({bs_code})")

                rs_idx = bs.query_history_k_data_plus(
                    bs_code,
                    "date,open,high,low,close,volume,amount",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d"
                )
                
                data_idx = []
                while (rs_idx.error_code == '0') & rs_idx.next():
                    data_idx.append(rs_idx.get_row_data())
                    
                if data_idx:
                    df_idx = pd.DataFrame(data_idx, columns=rs_idx.fields)
                    df_idx.rename(columns={
                        'date': '日期', 'close': f'{name}收盘价',
                        'open': '开盘价', 'high': '最高价', 'low': '最低价',
                        'volume': '成交量', 'amount': '成交额'
                    }, inplace=True)
                    
                    df_idx.to_csv(file_path, index=False, encoding='utf-8-sig')
                    success_count += 1
            
            print(f"✅ 阶段 2 完成！极速跳过无需更新的指数 {skip_count} 个，实际抓取并保存 {success_count} 个。")

            # ==========================================
            # 模块 1 & 2: 看板重点资产池 (采用同样的智能跳过)
            # ==========================================
            print("\n⏳ [阶段 3] 智能排查看板重点资产池...")
            for bs_code, name in TARGET_STOCKS.items():
                file_path_k = os.path.join(DATA_DIR, f"{name}.csv")
                
                # 智能跳过校验
                if os.path.exists(file_path_k):
                    try:
                        df_exist = pd.read_csv(file_path_k)
                        if not df_exist.empty and '日期' in df_exist.columns:
                            if str(df_exist['日期'].iloc[-1]) >= latest_trade_date:
                                print(f"  ⏭️ {name} 数据已是最新，光速跳过！")
                                continue
                    except Exception:
                        pass

                print(f"   - 发现 {name} 数据落后，正在重新对齐双重数据轴...")
            
                # ==================== [双重价格抓取与合并引擎] ====================
                # 1. 抓取前复权数据 (作为系统净值计算基准)
                rs_adj = bs.query_history_k_data_plus(
                    bs_code,
                    "date,open,high,low,close,volume,amount,turn,pctChg,peTTM,pbMRQ",
                    start_date="2023-01-01", 
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    frequency="d",
                    adjustflag="2" 
                )
                data_adj = []
                while (rs_adj.error_code == '0') & rs_adj.next():
                    data_adj.append(rs_adj.get_row_data())
                df_adj = pd.DataFrame(data_adj, columns=rs_adj.fields)

                # 2. 抓取不复权数据 (仅用来提取原始收盘价 raw_close)
                rs_raw = bs.query_history_k_data_plus(
                    bs_code,
                    "date,close", 
                    start_date="2023-01-01", 
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    frequency="d",
                    adjustflag="3" 
                )
                data_raw = []
                while (rs_raw.error_code == '0') & rs_raw.next():
                    data_raw.append(rs_raw.get_row_data())
                df_raw = pd.DataFrame(data_raw, columns=['date', 'raw_close'])

                # 3. 数据融合与落盘
                if not df_adj.empty and not df_raw.empty:
                    df_k = pd.merge(df_adj, df_raw, on='date', how='left')
                    df_k.rename(columns={
                        'date': '日期', 'close': f'{name}收盘价',
                        'open': '开盘价', 'high': '最高价', 'low': '最低价',
                        'volume': '成交量', 'amount': '成交额', 
                        'turn': '换手率', 'pctChg': '单日涨跌幅(%)', 
                        'peTTM': '市盈率(PE)', 'pbMRQ': '市净率(PB)'
                    }, inplace=True)
                    
                    os.makedirs(DATA_DIR, exist_ok=True) 
                    df_k.to_csv(os.path.join(DATA_DIR, f"{name}.csv"), index=False, encoding='utf-8-sig')
                    print(f"✅ {name} 行情同步成功。")

                    # 4. 抓取分红数据 (深度模糊匹配版)
                    os.makedirs(DIVIDEND_DIR, exist_ok=True)
                    try:
                        pure_code = bs_code.split('.')[1]
                        df_div = ak.stock_fhps_detail_em(symbol=pure_code)
                        
                        if not df_div.empty:
                            # 💡 更加激进的表头寻找策略
                            def find_col(keywords):
                                for col in df_div.columns:
                                    if any(k in col for k in keywords): return col
                                return None

                            c_date = find_col(['除权', '除息', '分红日', '派息日'])
                            c_cash = find_col(['派息', '现金', '分红', '派现'])
                            c_send = find_col(['送股', '送红股'])
                            c_trans = find_col(['转增', '转股'])

                            if c_date:
                                # 强制转换日期，无法转换的剔除
                                df_div[c_date] = pd.to_datetime(df_div[c_date], errors='coerce')
                                df_div = df_div.dropna(subset=[c_date])
                                
                                std_div = pd.DataFrame()
                                std_div['日期'] = df_div[c_date].dt.strftime('%Y-%m-%d')
                                
                                # 深度清洗数字：去掉“元”、“股”等杂质
                                def deep_clean(series):
                                    if series is None: return 0.0
                                    return pd.to_numeric(series.astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce').fillna(0.0)

                                std_div['每10股派息'] = deep_clean(df_div[c_cash])
                                std_div['每10股送股'] = deep_clean(df_div[c_send])
                                std_div['每10股转增'] = deep_clean(df_div[c_trans])
                                
                                # 过滤掉 2023 以后且真正有内容的分红
                                std_div = std_div[std_div['日期'] >= '2023-01-01']
                                std_div = std_div[(std_div['每10股派息'] > 0) | (std_div['每10股送股'] > 0) | (std_div['每10股转增'] > 0)]
                                
                                if not std_div.empty:
                                    std_div.to_csv(os.path.join(DIVIDEND_DIR, f"{name}_分红.csv"), index=False, encoding='utf-8-sig')
                                    print(f"   💰 {name} 成功抓取到 {len(std_div)} 条有效分红记录。")
                                else:
                                    print(f"   ℹ️ {name} 2023年后无已实施分红。")
                    except Exception as e:
                        print(f"   ⚠️ 分红抓取异常: {e}")
                
                else: # 💡 确保这个 else 紧跟在 if not df_adj.empty 的正下方
                    print(f"⚠️ {name} 行情抓取失败，请检查网络或代码。")
                # =================================================================
    
            bs.logout()

    # ==========================================
    # 模块 3: 实时盘中行情 (降维打击：纯血版新浪原生极速接口)
    # ==========================================
    print("\n⏳ [阶段 4] 正在绕过风控，通过底层通道截获实时行情...")
    try:
        import requests
        
        # 1. 自动拼接目标代码 (例如: sh.000001 -> sh000001)
        code_list = [k.replace('.', '') for k in TARGET_STOCKS.keys()]
        query_str = ",".join(code_list)
        
        # 2. 直接访问新浪底层极速行情服务器
        url = f"http://hq.sinajs.cn/list={query_str}"
        headers = {'Referer': 'https://finance.sina.com.cn/'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'  # 新浪的中文采用 GBK 编码
        
        realtime_data = []
        for line in response.text.strip().split('\n'):
            if not line or '="' not in line: continue
            if '="' in line:
                # 3. 极速拆解底层报文
                stock_code_raw = line.split('=')[0].split('_')[-1]
                data_str = line.split('="')[1].strip('";')
                items = data_str.split(',')
                
                # 👇 核心修复：增加长度防弹衣！过滤掉新浪返回的空数据或异常报文
                if len(items) < 4:
                    continue 
                
                # 新浪协议字段固定格式: [0]名称, [1]今日开盘, [2]昨日收盘, [3]当前现价
                name = items[0]
                
                # 强转浮点数时再加一层保护，防止新浪接口抽风返回非数字
                try:
                    current_price = float(items[3])
                    prev_close = float(items[2])
                except ValueError:
                    continue
                
                # 自动计算涨跌幅
                pct_change = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0
                
                realtime_data.append({
                    '代码': stock_code_raw,
                    '资产名称': name,
                    '最新价': current_price,
                    '涨跌幅(%)': round(pct_change, 2)
                })
                
        df_realtime = pd.DataFrame(realtime_data)
        if not df_realtime.empty:
            realtime_file = os.path.join(REALTIME_DIR, "realtime_snapshot.csv")
            df_realtime.to_csv(realtime_file, index=False, encoding='utf-8-sig')
            print(f"✅ 破防成功！截获了 {len(df_realtime)} 只资产的实时行情，彻底无视东方财富！")
        else:
            print("⚠️ 未解析到有效的实时行情数据。")
            
    except Exception as e:
        print(f"❌ 原生实时行情获取失败: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎉 所有智能抓取任务圆满完成！")

if __name__ == '__main__':
    
    from apscheduler.schedulers.blocking import BlockingScheduler
    import pytz

    # 强制锁定北京时间 (不受服务器本机时区影响)
    tz = pytz.timezone('Asia/Shanghai')
    scheduler = BlockingScheduler(timezone=tz)
    
    # 🎯 配置定时任务：每周一到周五（交易日）的 18:00 准时触发
    # 如果你想每天（包含周末）都运行，把 day_of_week='mon-fri' 删掉即可
    scheduler.add_job(fetch_data_now, 'cron', day_of_week='mon-fri', hour=18, minute=0)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ 自动化抓取服务已启动！")
    print(f"🌍 锁定计算时区: {tz}")
    print(f"⏰ 任务已装载，将在每个交易日的 18:00 准时执行...")
    
    try:
        # 启动调度器（程序会在这里阻塞挂起，像保安一样一直守着时间）
        scheduler.start() 
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 自动化服务已手动停止。")