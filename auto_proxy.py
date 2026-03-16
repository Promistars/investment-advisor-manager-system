import requests
import yaml
import os
import time
import subprocess

# 你的订阅链接
SUB_URL = "https://k4mxh.no-mad-world.club/link/RQrM6zprdzyC5YmW?clash=3"
LOCAL_PORT = 31080

def start_auto_proxy():
    print("⏳ 正在从订阅链接获取最新节点配置...")
    try:
        # 1. 发送请求获取配置 (伪装成浏览器防止被屏蔽)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(SUB_URL, headers=headers, timeout=15)
        response.raise_for_status() # 检查是否下载成功
        
        # 2. 解析 YAML 数据
        config = yaml.safe_load(response.text)
        proxies = config.get('proxies', [])
        
        # 3. 在列表中寻找第一个类型为 'ss' 的节点
        ss_node = None
        for p in proxies:
            if p.get('type') == 'ss':
                ss_node = p
                break  # 找到第一个 SS 节点就停止
                
        if not ss_node:
            print("❌ 解析失败：未在订阅中找到 'ss' 类型的节点！")
            return
            
        print(f"✅ 成功提取到节点信息：[{ss_node.get('name')}]")
        
        # 4. 提取启动 sslocal 所需的关键参数
        server = ss_node.get('server')
        port = ss_node.get('port')
        cipher = ss_node.get('cipher')
        password = ss_node.get('password')
        
        # 5. 组合启动命令 (适配最新版的 shadowsocks-rust 格式)
        # 注意：这里假设 sslocal 可执行文件和这个 Python 脚本在同一个目录下
        command = f'./sslocal -s "{server}:{port}" -b "127.0.0.1:{LOCAL_PORT}" -k "{password}" -m "{cipher}"'
        
        # 6. 杀死之前可能正在运行的旧代理进程 (防止 1080 端口被占用)
        print("🧹 正在清理旧的代理进程...")
        os.system("pkill -u $USER -f sslocal")
        time.sleep(2) # 停顿2秒，确保系统释放了端口
        
        # 7. 在后台静默启动新的代理服务
        print(f"🚀 正在后台启动专属 SOCKS5 代理服务 (端口: {LOCAL_PORT})...")
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"🎉 自动化完成！专属通道已在 127.0.0.1:{LOCAL_PORT} 开启。")

    except Exception as e:
        print(f"❌ 运行过程中发生错误: {e}")

if __name__ == "__main__":
    start_auto_proxy()