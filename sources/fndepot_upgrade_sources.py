import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime
import json

db_path='/var/apps/fndepot/var/fndepot.db'

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

def setup_proxy():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('http_proxy_enabled',))
        http_proxy_enabled = False
        if (setting and setting[0] and setting[0][0]):
            http_proxy_enabled = json.loads(setting[0] or setting[0][0])
        if (http_proxy_enabled):
            print(f"用户开启了http代理，跳过设置GitHub加速地址")
            return 
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('github_proxy_enabled',))      
        github_proxy_enabled = False
        if (setting and setting[0] and setting[0][0]):
            github_proxy_enabled = json.loads(setting[0][0])
        setting = querySql(cursor, "SELECT value FROM settings where key=?", ('github_proxy_url',))      
        github_proxy_url = ''
        if (setting and setting[0] and setting[0][0]):
            github_proxy_url = setting[0][0]
        if (github_proxy_enabled and ('http' in github_proxy_url)):
            print(f"用户已设置GitHub加速地址，跳过设置")
            return        
        now = datetime.now().isoformat()
        if (not github_proxy_enabled):
            cursor.execute("insert OR REPLACE into settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)", ('github_proxy_enabled', True, now, now,))
            print(f"开启GitHub加速")
        if (not 'http' in github_proxy_url):
            cursor.execute("insert OR REPLACE into settings (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)", ('github_proxy_url', 'https://ghfast.top\nhttps://gh.llkk.cc\nhttps://hk.gh-proxy.org\nhttps://gh-proxy.org\nhttps://hk.gh-proxy.org\nhttps://cdn.gh-proxy.org\nhttps://edgeone.gh-proxy.org', now, now,))
            print(f"设置github加速地址")

def upgrade_sources():    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # 从GitHub获取最新sources
        proxy_url = "https://ghfast.top"
        url = f"{proxy_url}/https://raw.githubusercontent.com/710850609/FnDepot/refs/heads/main/repo_list.txt"
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')
        
        # 处理并添加新sources
        insertCount = 0        
        now = datetime.now().isoformat()
        for line in data.splitlines():
            line = line.strip()
            # 提取name（域名后第一段路径值）
            parsed = urllib.parse.urlparse(line)
            path_segments = [s for s in parsed.path.split('/') if s]
            name = path_segments[0] if path_segments else ''
            cursor.execute("INSERT OR IGNORE INTO sources (url, name, is_default, is_builtin, priority, sync_status, last_sync, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (line, name, False, False, '100', 'synced', None, now, now,))
            insertCount += cursor.rowcount
            if (insertCount > 0):
                print(f"添加源: {line}")
    print(f"更新了 {insertCount} 条源")

if __name__ == "__main__":
    setup_proxy()
    upgrade_sources()