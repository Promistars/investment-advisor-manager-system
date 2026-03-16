import os
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
import baostock as bs
import akshare as ak

# 配置你的数据文件夹路径
DATA_DIR = "financial_data"

def fetch_data_baostock(stock_code, start_date, end_date):
    """
    备用引擎：使用 BaoStock 抓取数据（极度抗封锁）
    stock_code 格式：'sh.000300', 'sz.000001'
    """
    bs.login() # 登录系统（免费开源，无需账号）
    # 获取日线数据
    rs = bs.query_history_k_data_plus(
        stock_code,
        "date,close",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3" # 3为后复权
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    bs.logout()
    
    if not data_list:
        return pd.DataFrame()
        
    df = pd.DataFrame(data_list, columns=rs.fields)
    df.rename(columns={'date': '日期', 'close': '收盘价'}, inplace=True)
    df['收盘价'] = df['收盘价'].astype(float)
    return df

def fetch_data_akshare_tencent(stock_code):
    """
    主力引擎：使用 AkShare 的腾讯接口抓取（比东方财富抗墙能力强）
    stock_code 格式：'sh000300', 'sz000001'
    """
    try:
        # 使用腾讯的日线接口，通常没有严格的 IP 封锁
        df = ak.stock_zh_a_daily(symbol=stock_code, adjust="hfq")
        df = df.reset_index()
        df = df[['date', 'close']]
        df.rename(columns={'date': '日期', 'close': '收盘价'}, inplace=True)
        return df
    except Exception as e:
        print(f"AkShare 抓取失败: {e}")
        return pd.DataFrame()

def daily_update_job():
    """这是每天下午 6 点会执行的核心任务"""
    print(f"[{datetime.now()}] 🚀 开始执行每日量化数据拉取任务...")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # 假设我们需要更新沪深300（基准）和平安银行（示例资产）
    # 你可以根据实际情况，去遍历 financial_data 文件夹下的已有 csv，提取代码进行更新
    target_stocks = {
        'sh000300': '沪深300',
        'sz000001': '平安银行',
        # 在这里添加你需要监控的标的字典...
    }
    
    for code, name in target_stocks.items():
        print(f"正在抓取: {name} ({code})...")
        
        # 优先尝试使用 AkShare 腾讯接口，如果失败则启用 BaoStock 备用
        df = fetch_data_akshare_tencent(code)
        
        if df.empty:
            print(f"⚠️ 切换到 BaoStock 备用线路抓取 {name}...")
            # BaoStock 代码格式需要加点，例如 sh000300 -> sh.000300
            bs_code = f"{code[:2]}.{code[2:]}" 
            # 抓取最近一年的数据即可，或者自定义区间
            df = fetch_data_baostock(bs_code, start_date="2023-01-01", end_date=datetime.now().strftime("%Y-%m-%d"))
            
        if not df.empty:
            # 适配你的底层系统，将列名改为 {资产名}收盘价
            df.rename(columns={'收盘价': f'{name}收盘价'}, inplace=True)
            # 确保日期格式为 datetime
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            
            # 保存到 financial_data 文件夹
            file_path = os.path.join(DATA_DIR, f"{code}.csv")
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"✅ {name} 数据已更新并保存至 {file_path}")
        else:
            print(f"❌ {name} 数据更新失败！")

    print(f"[{datetime.now()}] 🎉 每日数据拉取任务完成！\n")

# ==========================================
# 启动定时调度器
# ==========================================
if __name__ == '__main__':
    # 强制设置时区为上海（北京时间），不受服务器所在地的 UTC 时间影响
    tz = pytz.timezone('Asia/Shanghai')
    scheduler = BlockingScheduler(timezone=tz)
    
    # 配置任务：每周一到周五的 18:00 准时运行
    scheduler.add_job(daily_update_job, 'cron', day_of_week='mon-fri', hour=18, minute=0)
    
    print(f"⏳ 自动化数据更新服务已启动...")
    print(f"🕒 当前服务器设定时区: {tz}")
    print(f"🎯 下一次执行时间: {scheduler.get_jobs()[0].next_run_time}")
    
    try:
        scheduler.start() # 阻塞在此处，保持进程一直运行
    except (KeyboardInterrupt, SystemExit):
        print("服务已停止。")