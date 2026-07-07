#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" 版本V3 """
import json
import logging
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime
import shlex
import csv

import dns.resolver

# github 加速地址
db_path='/var/apps/fndepot/var/fndepot.db'
manifest_path='/var/apps/fndepot/manifest'


def querySql(cursor, sql, params):
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    data = []
    for row in rows:
        colData = []
        for col in row:
            colData.append(col)
        data.append(colData)
    return data

def get_github_proxy_url():
    """获取GitHub加速地址"""
    records = []
    try:
        answers = dns.resolver.resolve('github-proxy.v6.army', 'TXT', lifetime=5)
        for rdata in answers:
            # TXT 记录可能包含多个字符串段，拼接起来
            txt = ''.join([s.decode('utf-8') for s in rdata.strings])
            records.append(txt)
        logging.info(f"获取GitHub加速地址: {len(records)} 个")
        return records
    except dns.resolver.NXDOMAIN:
        pass  # 域名不存在
    except dns.resolver.NoAnswer:
        pass  # 无 TXT 记录
    except dns.resolver.LifetimeTimeout:
        pass  # DNS 查询超时
    except Exception as e:
        raise
    if not records or len(records) == 0:
        logging.warning("DNS TXT 查询返回空，使用内置加速地址")
        url_list = [
            "https://ghfast.top",
            "https://gh-proxy.com",
            "https://gh.llkk.cc",
        ]
    return records


def check_install_fndepot():
    """检查是否安装了FnDepot"""
    if not os.path.exists(db_path):
        logging.error(f"未安装FnDepot")
        return False
    with open(manifest_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # 使用 shlex 安全解析
    reader = csv.reader(shlex.split(text, posix=False), delimiter='=')
    config = {key: value for key, value in reader}
    version = config.get('version', '')
    require_version = '0.0.7'
    if str(version) < require_version:
        logging.error(f"FnDepot当前版本: {version}，不支持自动注入。请安装 {require_version} 版本 FnDepot")
        return False
    return True

def setup_proxy(github_proxy_urls: list[str]):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('http_proxy_enabled',))
        http_proxy_enabled = False
        if setting and setting[0] and setting[0][0]:
            http_proxy_enabled = json.loads(setting[0][0])
        if http_proxy_enabled:
            logging.info(f"用户开启了http代理，跳过设置GitHub加速地址")
            return 
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('github_proxy_enabled',))      
        github_proxy_enabled = False
        if setting and setting[0] and setting[0][0]:
            github_proxy_enabled = json.loads(setting[0][0])
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('github_proxy_url',))      
        github_proxy_url = ''
        if setting and setting[0] and setting[0][0]:
            github_proxy_url = setting[0][0]
        # if github_proxy_enabled and ('http' in github_proxy_url):
        #     logging.info(f"用户已设置GitHub加速地址，跳过设置")
        #     return
        now = datetime.now().isoformat()
        if not github_proxy_enabled:
            cursor.execute("insert OR REPLACE into settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)", ('github_proxy_enabled', True, now, now,))
            logging.info(f"开启GitHub加速")
        save_urls = [url.strip() for url in github_proxy_url.split('\n')]
        append_urls = [url.strip() for url in github_proxy_urls if url not in save_urls]

        if len(append_urls) > 0:
            values = '\n'.join(save_urls + append_urls)
            cursor.execute("insert OR REPLACE into settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)", ('github_proxy_url', values, now, now,))
            logging.info(f"追加GitHub加速地址：{append_urls}")
        else:
            logging.info(f"已有提供的GitHub加速地址，跳过设置")

def upgrade_sources(github_proxy_urls: list[str]):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # 从GitHub获取最新sources，逐一尝试代理地址
        raw_url = "https://raw.githubusercontent.com/710850609/FnDepot/refs/heads/main/repo_list.txt"
        data = None
        last_error = None
        for proxy_url in github_proxy_urls:
            url = f"{proxy_url}/{raw_url}" if proxy_url else raw_url
            try:
                logging.info(f"尝试下载: {url}")
                response = urllib.request.urlopen(url, timeout=30)
                data = response.read().decode('utf-8')
                logging.info(f"下载源成功")
                break
            except Exception as e:
                last_error = e
                logging.warning(f"下载失败: {url}, 错误: {e}")
        if data is None:
            raise Exception(f"所有代理地址下载失败: {last_error}")
        
        # 处理并添加新sources
        insertCount = 0        
        now = datetime.now().isoformat()
        lines = data.splitlines()
        logging.info(f"共获取到 {len(lines)} 条源")
        for line in lines:
            line = line.strip()
            # 提取name（域名后第一段路径值）
            parsed = urllib.parse.urlparse(line)
            path_segments = [s for s in parsed.path.split('/') if s]
            name = path_segments[0] if path_segments else ''
            cursor.execute("SELECT 1 FROM sources WHERE url = ?", (line,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO sources (url, name, is_default, is_builtin, priority, sync_status, last_sync, sync_enabled, is_fork, source_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (line, name, False, False, '100', 'synced', None, True, False, 0, now, now))
                insertCount += 1
                logging.info(f"添加源: {line}")
            else:
                # logging.info(f"已存在源: `{line}`")
                pass
    logging.info(f"更新了 {insertCount} 条源")

def run(log_file=None):
    if log_file:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=log_file,
            filemode='a',
            encoding='utf-8'
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            stream=sys.stderr
        )
    if not check_install_fndepot():
        return
    # sleep(60)
    proxy_urls = get_github_proxy_url()
    setup_proxy(proxy_urls)
    upgrade_sources(proxy_urls)

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else None
    run(log_file)