import os
import pandas as pd
from datetime import datetime, timedelta
import baostock as bs
import akshare as ak
import time
import json

# ==========================================
# 🎯 核心配置：动态股票池读取引擎
# ==========================================
CONFIG_FILE = "stock_config.json"
DATA_DIR = "financial_data"        # 存放你的核心个股和上证指数
FUNDA_DIR = "fundamental_data"     # 存放财务基本面数据
REALTIME_DIR = "realtime_data"     # 存放实时行情快照
INDEX_DIR = "all_indices_data"     # 存放全市场数百个指数的独立历史文件
DIVIDEND_DIR = "dividend_data"     # 存放历史分红派息事件库

for d in [DATA_DIR, FUNDA_DIR, REALTIME_DIR, INDEX_DIR, DIVIDEND_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

DEFAULT_STOCKS = {
    'sh.601318': '中国平安',
    'sh.600519': '贵州茅台',
    'sh.601658': '邮储银行',
    'sh.600036': '招商银行',
}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        TARGET_STOCKS = json.load(f)
else:
    TARGET_STOCKS = DEFAULT_STOCKS
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(TARGET_STOCKS, f, ensure_ascii=False, indent=4)

TX_STOCKS = {k.replace('.', ''): v for k, v in TARGET_STOCKS.items()}


def get_latest_trading_date_bs():
    """通过 BaoStock 探测最新交易日"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    rs = bs.query_history_k_data_plus("sh.000001", "date", start_date=start_date, end_date=end_date, frequency="d")
    dates = []
    while (rs.error_code == '0') & rs.next():
        dates.append(rs.get_row_data()[0])
    return dates[-1] if dates else end_date


def get_latest_trading_date_ak():
    """通过 AKShare 探测最新交易日（BaoStock 不可用时的备用）"""
    try:
        df = ak.stock_zh_a_hist(symbol='601318', period='daily',
                                 start_date=(datetime.now() - timedelta(days=14)).strftime('%Y%m%d'),
                                 end_date=datetime.now().strftime('%Y%m%d'), adjust='')
        return str(df['日期'].iloc[-1]) if not df.empty else datetime.now().strftime('%Y-%m-%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def fetch_data_now():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 启动智能增量抓取引擎...")

    # ==========================================
    # 阶段 1: 获取全市场指数清单（AKShare，始终可用）
    # ==========================================
    print("\n⏳ [阶段 1] 正在获取全市场指数清单...")
    try:
        df_indices = ak.stock_zh_index_spot_sina()
        total_indices = len(df_indices)
        print(f"✅ 成功发现 {total_indices} 个指数。")
    except Exception as e:
        print(f"❌ 获取指数列表失败: {e}")
        df_indices = pd.DataFrame()

    # ==========================================
    # 尝试登录 BaoStock（最优渠道，失败则纯走 AKShare）
    # ==========================================
    lg = bs.login()
    bs_ok = (lg.error_code == '0')
    if bs_ok:
        latest_trade_date = get_latest_trading_date_bs()
        print(f"📌 BaoStock 连接正常，最新交易日: 【{latest_trade_date}】")
    else:
        print(f"⚠️ BaoStock 不可用 ({lg.error_msg})，切换至纯 AKShare 模式...")
        latest_trade_date = get_latest_trading_date_ak()
        print(f"📌 AKShare 探测最新交易日: 【{latest_trade_date}】")

    # ==========================================
    # 阶段 2: 全市场指数历史数据（BaoStock 优先，AKShare 兜底）
    # ==========================================
    if not df_indices.empty:
        print(f"\n⏳ [阶段 2] 开始智能排查与抓取 {total_indices} 个指数 (2023年至今)...")
        start_date = "2023-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
        success_count = 0
        skip_count = 0

        for i, row in df_indices.iterrows():
            code = row['代码']
            name = str(row['名称'])

            if not (str(code).startswith('sh') or str(code).startswith('sz')):
                continue

            bs_code = f"{code[:2]}.{code[2:]}"
            safe_name = name.replace('/', '_').replace('\\', '_').replace('*', '').replace('?', '')
            file_path = os.path.join(INDEX_DIR, f"{safe_name}.csv")

            # 智能跳过：文件已是最新则跳过
            if os.path.exists(file_path):
                try:
                    df_exist = pd.read_csv(file_path)
                    if not df_exist.empty and '日期' in df_exist.columns:
                        if str(df_exist['日期'].iloc[-1]) >= latest_trade_date:
                            skip_count += 1
                            continue
                except Exception:
                    pass

            if (success_count + 1) % 10 == 0:
                print(f"  🔄 正在抓取: {name} ({bs_code})")

            saved = False

            # 主力：BaoStock
            if bs_ok:
                rs_idx = bs.query_history_k_data_plus(
                    bs_code, "date,open,high,low,close,volume,amount",
                    start_date=start_date, end_date=end_date, frequency="d"
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
                    saved = True

            # 备用：AKShare
            if not saved:
                try:
                    df_ak_idx = ak.stock_zh_index_daily(symbol=code)
                    if not df_ak_idx.empty:
                        df_ak_idx = df_ak_idx[df_ak_idx['date'].astype(str) >= start_date].copy()
                        df_ak_idx.rename(columns={
                            'date': '日期', 'close': f'{name}收盘价',
                            'open': '开盘价', 'high': '最高价', 'low': '最低价',
                            'volume': '成交量', 'amount': '成交额'
                        }, inplace=True)
                        df_ak_idx['日期'] = df_ak_idx['日期'].astype(str)
                        df_ak_idx.to_csv(file_path, index=False, encoding='utf-8-sig')
                        success_count += 1
                except Exception:
                    pass

        print(f"✅ 阶段 2 完成！跳过 {skip_count} 个，实际抓取 {success_count} 个。")

    # ==========================================
    # 阶段 3: 看板重点资产池（BaoStock 优先，AKShare 兜底）
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

        # 读取现有文件，确定增量起点
        df_exist_k = pd.DataFrame()
        if os.path.exists(file_path_k):
            try:
                df_exist_k = pd.read_csv(file_path_k)
            except Exception:
                pass
        if not df_exist_k.empty and '日期' in df_exist_k.columns:
            last_exist = str(df_exist_k['日期'].iloc[-1])
            fetch_start = (datetime.strptime(last_exist[:10], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            fetch_start = "2023-01-01"
            df_exist_k = pd.DataFrame()
        fetch_end = datetime.now().strftime("%Y-%m-%d")

        df_adj = pd.DataFrame()
        df_raw_bs = pd.DataFrame()

        # 主力渠道：BaoStock (含 PE/PB、前复权)
        if bs_ok:
            rs_adj = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg,peTTM,pbMRQ",
                start_date=fetch_start, end_date=fetch_end,
                frequency="d", adjustflag="2"
            )
            data_adj = []
            while (rs_adj.error_code == '0') & rs_adj.next():
                data_adj.append(rs_adj.get_row_data())
            if data_adj:
                df_adj = pd.DataFrame(data_adj, columns=rs_adj.fields)

            rs_raw = bs.query_history_k_data_plus(
                bs_code, "date,close",
                start_date=fetch_start, end_date=fetch_end,
                frequency="d", adjustflag="3"
            )
            data_raw = []
            while (rs_raw.error_code == '0') & rs_raw.next():
                data_raw.append(rs_raw.get_row_data())
            if data_raw:
                df_raw_bs = pd.DataFrame(data_raw, columns=['date', 'raw_close'])

        # 备用渠道：AKShare（BaoStock 无数据时自动切换）
        if df_adj.empty:
            print(f"     ⚠️ BaoStock 无数据，切换至 AKShare 备用渠道...")
            try:
                pure_code = bs_code.split('.')[1]
                fetch_start_ak = fetch_start.replace('-', '')
                fetch_end_ak = fetch_end.replace('-', '')
                df_ak_qfq = ak.stock_zh_a_hist(symbol=pure_code, period='daily',
                                                start_date=fetch_start_ak, end_date=fetch_end_ak, adjust='qfq')
                df_ak_raw = ak.stock_zh_a_hist(symbol=pure_code, period='daily',
                                                start_date=fetch_start_ak, end_date=fetch_end_ak, adjust='')
                if not df_ak_qfq.empty:
                    df_adj = df_ak_qfq.rename(columns={
                        '日期': 'date', '收盘': 'close', '开盘': 'open',
                        '最高': 'high', '最低': 'low', '成交量': 'volume',
                        '成交额': 'amount', '换手率': 'turn', '涨跌幅': 'pctChg'
                    })
                    df_adj['date'] = df_adj['date'].astype(str)
                    df_adj['peTTM'] = ''
                    df_adj['pbMRQ'] = ''
                if not df_ak_raw.empty:
                    df_raw_bs = df_ak_raw[['日期', '收盘']].rename(columns={'日期': 'date', '收盘': 'raw_close'})
                    df_raw_bs['date'] = df_raw_bs['date'].astype(str)
            except Exception as e_ak:
                print(f"     ❌ AKShare 备用渠道也失败: {e_ak}")

        # 数据融合与落盘
        if not df_adj.empty:
            if not df_raw_bs.empty:
                df_k_new = pd.merge(df_adj, df_raw_bs, on='date', how='left')
            else:
                df_k_new = df_adj.copy()
                df_k_new['raw_close'] = df_k_new['close']
            df_k_new.rename(columns={
                'date': '日期', 'close': f'{name}收盘价',
                'open': '开盘价', 'high': '最高价', 'low': '最低价',
                'volume': '成交量', 'amount': '成交额',
                'turn': '换手率', 'pctChg': '单日涨跌幅(%)',
                'peTTM': '市盈率(PE)', 'pbMRQ': '市净率(PB)'
            }, inplace=True)

            df_final = pd.concat([df_exist_k, df_k_new], ignore_index=True)
            os.makedirs(DATA_DIR, exist_ok=True)
            df_final.to_csv(os.path.join(DATA_DIR, f"{name}.csv"), index=False, encoding='utf-8-sig')
            print(f"✅ {name} 行情同步成功（新增 {len(df_k_new)} 行）。")

            # 抓取分红数据
            os.makedirs(DIVIDEND_DIR, exist_ok=True)
            try:
                pure_code = bs_code.split('.')[1]
                df_div = ak.stock_fhps_detail_em(symbol=pure_code)
                if not df_div.empty:
                    def find_col(keywords):
                        for col in df_div.columns:
                            if any(k in col for k in keywords): return col
                        return None

                    c_date = find_col(['除权', '除息', '分红日', '派息日'])
                    c_cash = find_col(['派息', '现金', '分红', '派现'])
                    c_send = find_col(['送股', '送红股'])
                    c_trans = find_col(['转增', '转股'])

                    if c_date:
                        df_div[c_date] = pd.to_datetime(df_div[c_date], errors='coerce')
                        df_div = df_div.dropna(subset=[c_date])
                        std_div = pd.DataFrame()
                        std_div['日期'] = df_div[c_date].dt.strftime('%Y-%m-%d')

                        def deep_clean(series):
                            if series is None: return 0.0
                            return pd.to_numeric(series.astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce').fillna(0.0)

                        std_div['每10股派息'] = deep_clean(df_div[c_cash])
                        std_div['每10股送股'] = deep_clean(df_div[c_send])
                        std_div['每10股转增'] = deep_clean(df_div[c_trans])
                        std_div = std_div[std_div['日期'] >= '2023-01-01']
                        std_div = std_div[(std_div['每10股派息'] > 0) | (std_div['每10股送股'] > 0) | (std_div['每10股转增'] > 0)]
                        if not std_div.empty:
                            std_div.to_csv(os.path.join(DIVIDEND_DIR, f"{name}_分红.csv"), index=False, encoding='utf-8-sig')
                            print(f"   💰 {name} 成功抓取到 {len(std_div)} 条有效分红记录。")
                        else:
                            print(f"   ℹ️ {name} 2023年后无已实施分红。")
            except Exception as e:
                print(f"   ⚠️ 分红抓取异常: {e}")
        else:
            print(f"⚠️ {name} 行情抓取失败，请检查网络或代码。")

    if bs_ok:
        bs.logout()

    # ==========================================
    # 阶段 4: 实时盘中行情（新浪底层接口，始终可用）
    # ==========================================
    print("\n⏳ [阶段 4] 正在绕过风控，通过底层通道截获实时行情...")
    try:
        import requests
        code_list = [k.replace('.', '') for k in TARGET_STOCKS.keys()]
        query_str = ",".join(code_list)
        url = f"http://hq.sinajs.cn/list={query_str}"
        headers = {'Referer': 'https://finance.sina.com.cn/'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'

        realtime_data = []
        for line in response.text.strip().split('\n'):
            if not line or '="' not in line: continue
            stock_code_raw = line.split('=')[0].split('_')[-1]
            data_str = line.split('="')[1].strip('";')
            items = data_str.split(',')
            if len(items) < 4:
                continue
            r_name = items[0]
            try:
                current_price = float(items[3])
                prev_close = float(items[2])
            except ValueError:
                continue
            pct_change = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0
            realtime_data.append({
                '代码': stock_code_raw,
                '资产名称': r_name,
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

    tz = pytz.timezone('Asia/Shanghai')
    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_job(fetch_data_now, 'cron', day_of_week='mon-fri', hour=18, minute=0)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ 自动化抓取服务已启动！")
    print(f"🌍 锁定计算时区: {tz}")
    print(f"⏰ 任务已装载，将在每个交易日的 18:00 准时执行...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 自动化服务已手动停止。")
