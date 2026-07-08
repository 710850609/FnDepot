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
import subprocess

import dns.resolver

# github 加速地址
db_path='/var/apps/fndepot/var/fndepot.db'
manifest_path='/var/apps/fndepot/manifest'
SCHEDULE_FILE = f"/vol1/@appcenter/fndepot.source/backend/tasks/schedule.json"


def setup_logging(log_file=None):
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


def get_github_proxy_url():
    """获取GitHub加速地址"""
    try:
        answers = dns.resolver.resolve('github-proxy.v6.army', 'TXT', lifetime=5)
        records = []
        for rdata in answers:
            txt = ''.join([s.decode('utf-8') for s in rdata.strings])
            records.append(txt)
        logging.info(f"获取GitHub加速地址: {len(records)} 个")
        return records
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.LifetimeTimeout:
        pass
    except Exception as e:
        raise
    logging.warning("DNS TXT 查询返回空，使用内置加速地址")
    return [
        "https://ghfast.top",
        "https://gh-proxy.com",
        "https://gh.llkk.cc",
    ]


def check_install_fndepot():
    """检查是否安装了FnDepot"""
    if not os.path.exists(db_path):
        logging.error(f"未安装FnDepot")
        return False
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            text = f.read()
        reader = csv.reader(shlex.split(text, posix=False), delimiter='=')
        config = {key: value for key, value in reader}
        version = config.get('version', '')
    except Exception as e:
        logging.error(f"读取FnDepot manifest失败: {e}")
        return False
    require_version = '0.0.7'
    if str(version) < require_version:
        logging.error(f"FnDepot当前版本: {version}，不支持自动注入。请安装 {require_version} 版本 FnDepot")
        return False
    return True

def setup_proxy(github_proxy_urls: list[str]):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        row = cursor.execute("SELECT value FROM settings WHERE key=?", ('http_proxy_enabled',)).fetchone()
        if row and row['value']:
            if json.loads(row['value']):
                logging.info(f"用户开启了http代理，跳过设置GitHub加速地址")
                return

        row = cursor.execute("SELECT value FROM settings WHERE key=?", ('github_proxy_enabled',)).fetchone()
        github_proxy_enabled = json.loads(row['value']) if row and row['value'] else False

        row = cursor.execute("SELECT value FROM settings WHERE key=?", ('github_proxy_url',)).fetchone()
        github_proxy_url = row['value'] if row and row['value'] else ''

        now = datetime.now().isoformat()
        if not github_proxy_enabled:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
                           ('github_proxy_enabled', 'true', now, now))
            logging.info(f"开启GitHub加速")

        save_urls = [u for u in github_proxy_url.split('\n') if u.strip()]
        append_urls = [u for u in github_proxy_urls if u not in save_urls]

        if append_urls:
            values = '\n'.join(save_urls + append_urls)
            cursor.execute("INSERT OR REPLACE INTO settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
                           ('github_proxy_url', values, now, now))
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
    setup_logging(log_file)
    if not check_install_fndepot():
        return
    # sleep(60)
    proxy_urls = get_github_proxy_url()
    setup_proxy(proxy_urls)
    upgrade_sources(proxy_urls)


def notify_upgrade(log_file=None):
    """查询需要更新的应用，推送系统通知"""
    setup_logging(log_file)

    if not os.path.exists(db_path):
        logging.error(f"FnDepot数据库不存在: {db_path}")
        return

    last_check_update_time = None
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)
            last_check_update_time = schedule_data.get('last_check_update_time')
        except Exception:
            pass

    query = "SELECT display_name, latest_version, max(last_update) as last_update_time FROM apps WHERE installed_version < latest_version"
    params = []
    if last_check_update_time:
        query += " AND last_update > ?"
        params = [last_check_update_time]
        logging.info(f"防重过滤: last_update > {last_check_update_time}")
    query += " GROUP BY display_name, latest_version"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        logging.info("没有需要更新的应用，跳过系统通知")
        return

    push_lines = []
    for row in rows:
        push_lines.append(f"{row['display_name']}  有新版本 {row['latest_version']}")
    push_text = '\n'.join(push_lines)
    logging.info(f"待推送通知，共 {len(rows)} 个应用:\n{push_text}")

    escaped_text = push_text.replace("'", "''")
    sql = (
        "WITH new_notify AS ("
        " INSERT INTO notify (cat, level, title, source, content, dateandtime)"
        " VALUES (0, 0, 'Depot应用源提醒', 'fndepot.source',"
        f" '{escaped_text}', extract(epoch from now())::bigint)"
        " RETURNING id"
        ")"
        " INSERT INTO notify_user (uid, notify_id, read)"
        " SELECT uid, new_notify.id, 0 FROM users, new_notify;"
    )

    cmd = ['psql', '-U', 'postgres', '-d', 'trim', '-c', sql]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logging.info(f"系统通知推送成功，共 {len(rows)} 个应用更新")
            last_update_time = max(row['last_update_time'] for row in rows if row['last_update_time']) if rows else None
            if last_update_time and os.path.exists(SCHEDULE_FILE):
                try:
                    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                        schedule_data = json.load(f)
                    schedule_data['last_check_update_time'] = last_update_time
                    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(schedule_data, f, ensure_ascii=False)
                    logging.info(f"已更新 last_check_update_time: {last_update_time}")
                except Exception as e:
                    logging.exception(f"更新 SCHEDULE_FILE 失败: {e}")
        else:
            logging.error(f"系统通知推送失败: {result.stderr}")
    except Exception as e:
        logging.exception(f"系统通知推送异常: {e}")


if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else None
    mode = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == 'notify_upgrade':
        notify_upgrade(log_file)
    else:
        run(log_file)