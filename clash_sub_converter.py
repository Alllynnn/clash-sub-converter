# -*- coding: utf-8 -*-

import os
import requests
import base64
import sys
import re
import yaml
import subprocess
import time
import signal
import atexit
from urllib.parse import quote

# 配置信息
SUBCONVERTER_URL = "http://127.0.0.1:25500/sub"  # subconverter的地址，根据实际情况修改
OUTPUT_FILE = "merged_config.yaml"  # 输出的配置文件名
TARGET_TYPE = "clash"  # 目标配置类型，可根据需要修改
DEFAULT_LINKS_FILE = "links.txt"  # 默认的订阅链接文件
SUBCONVERTER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subconverter", "subconverter.exe")

# 全局变量存储subconverter进程
subconverter_process = None

# 过滤规则列表
FILTER_KEYWORDS = [
    "距离下次重置", 
    "剩余",
    "天",
    "网址",
    "导航",
    "超时请更新订阅",
    "亲！",
    "更新订阅是好习惯",
    "ChatGPT请使用",
    "山水导航",
    "自由猫",
    ".com",
    "请使用",
    "使用教程",
    "过期",
    "失效",
    "官网",
    "联系方式",
    "电报群",
    "交流群",
    "最新网址"
]

# 正则表达式过滤模式
FILTER_PATTERNS = [
    r'距离.*?重置.*?天',
    r'剩余.*?天',
    r'网址.*?com',
    r'.*?官网.*?',
    r'.*?交流群.*?',
    r'.*?邀请码.*?',
    r'.*?过期.*?天'
]

def start_subconverter():
    """启动subconverter服务"""
    global subconverter_process
    
    if not os.path.exists(SUBCONVERTER_PATH):
        print(f"错误：未找到subconverter可执行文件: {SUBCONVERTER_PATH}")
        return False
    
    try:
        print("正在启动subconverter服务...")
        # 使用subprocess.Popen启动子进程，并设置不显示窗口
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
        
        subconverter_process = subprocess.Popen(
            [SUBCONVERTER_PATH],
            cwd=os.path.dirname(SUBCONVERTER_PATH),
            startupinfo=startupinfo
        )
        
        # 等待服务启动
        for _ in range(10):
            try:
                response = requests.get("http://127.0.0.1:25500/version")
                if response.status_code == 200:
                    print("subconverter服务已启动")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("启动subconverter服务超时")
        return False
    except Exception as e:
        print(f"启动subconverter服务失败: {str(e)}")
        return False

def stop_subconverter():
    """停止subconverter服务"""
    global subconverter_process
    
    if subconverter_process:
        print("正在停止subconverter服务...")
        try:
            if sys.platform == "win32":
                subconverter_process.terminate()
            else:
                os.kill(subconverter_process.pid, signal.SIGTERM)
            subconverter_process.wait(timeout=5)
            print("subconverter服务已停止")
        except Exception as e:
            print(f"停止subconverter服务时出错: {str(e)}")
            try:
                if sys.platform == "win32":
                    os.system(f"taskkill /F /PID {subconverter_process.pid}")
                else:
                    os.kill(subconverter_process.pid, signal.SIGKILL)
                print("已强制终止subconverter服务")
            except:
                pass

def read_subscription_links(file_path):
    """从文本文件中读取订阅链接"""
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f.readlines() if line.strip()]
    
    return links

def merge_subscriptions(links):
    """合并多个订阅链接的内容"""
    if not links:
        print("没有找到有效的订阅链接")
        return None
    
    # 将所有链接合并为一个，用|分隔
    merged_url = '|'.join(links)
    
    # 使用subconverter进行转换
    params = {
        'target': TARGET_TYPE,
        'url': merged_url,
        'emoji': 'true',
        'list': 'false',
        'udp': 'true',
        'tfo': 'false',
        'scv': 'false',
        'fdn': 'false',
        'sort': 'false'
    }
    
    try:
        response = requests.get(SUBCONVERTER_URL, params=params)
        if response.status_code == 200:
            return response.text
        else:
            print(f"转换失败，HTTP状态码: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return None

def should_filter_node(node_name):
    """判断节点是否应该被过滤"""
    # 关键词过滤
    for keyword in FILTER_KEYWORDS:
        if keyword in node_name:
            return True
    
    # 正则表达式过滤
    for pattern in FILTER_PATTERNS:
        if re.search(pattern, node_name):
            return True
    
    # 是否存在过多的特殊字符（广告特征）
    special_chars = sum(1 for c in node_name if c in '!！，,？?♥★☆')
    if special_chars > 2:  # 如果特殊字符超过2个，可能是广告
        return True
    
    return False

def filter_nodes(config_content):
    """过滤掉含有广告或无用信息的节点"""
    try:
        # 解析YAML内容
        config = yaml.safe_load(config_content)
        
        if 'proxies' not in config:
            print("配置文件中未找到节点信息")
            return config_content
        
        original_count = len(config['proxies'])
        
        # 过滤节点
        filtered_proxies = []
        filtered_names = []
        ad_nodes = []
        
        for proxy in config['proxies']:
            # 跳过包含过滤关键词的节点
            if should_filter_node(proxy['name']):
                ad_nodes.append(proxy['name'])
                continue
            
            filtered_proxies.append(proxy)
            filtered_names.append(proxy['name'])
        
        # 更新节点列表
        config['proxies'] = filtered_proxies
        
        # 更新代理组中的节点引用
        if 'proxy-groups' in config:
            for group in config['proxy-groups']:
                if 'proxies' in group:
                    group['proxies'] = [proxy for proxy in group['proxies'] 
                                     if proxy in ['DIRECT', 'REJECT', 'GLOBAL', '🎯 全球直连', '🛑 全球拦截', '♻️ 自动选择', '🔰 节点选择']
                                     or proxy in filtered_names]
        
        filtered_count = len(config['proxies'])
        removed_count = original_count - filtered_count
        
        print(f"过滤前节点数量: {original_count}, 过滤后节点数量: {filtered_count}, 过滤掉: {removed_count}个广告/无用节点")
        
        if removed_count > 0 and removed_count <= 10:
            print("已过滤的广告节点:")
            for node in ad_nodes:
                print(f"- {node}")
        
        # 转换回YAML文本
        return yaml.dump(config, allow_unicode=True, sort_keys=False)
    
    except Exception as e:
        print(f"过滤节点时出错: {str(e)}")
        return config_content

def save_config(content, output_file):
    """保存配置到文件"""
    if not content:
        return False
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"配置已保存到 {output_file}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {str(e)}")
        return False

def main():
    # 注册退出时停止subconverter服务
    atexit.register(stop_subconverter)
    
    # 启动subconverter服务
    if not start_subconverter():
        print("无法启动subconverter服务，程序退出")
        return
    
    # 如果命令行指定了文件路径，则使用指定的路径，否则使用默认路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = DEFAULT_LINKS_FILE
        print(f"未指定文件路径，使用默认文件：{DEFAULT_LINKS_FILE}")
    
    links = read_subscription_links(file_path)
    
    if not links:
        return
    
    print(f"找到 {len(links)} 个订阅链接")
    content = merge_subscriptions(links)
    
    if content:
        # 过滤节点
        filtered_content = filter_nodes(content)
        save_config(filtered_content, OUTPUT_FILE)

if __name__ == "__main__":
    main()