#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import subprocess
import sys
from datetime import datetime

TASK_LOG_FILE = f"/var/apps/fndepot.source/var/logs/tasks.log"
APP_LOG_FILE = f"/var/apps/fndepot.source/var/logs/app.log"
SCHEDULE_FILE = f"/vol1/@appcenter/fndepot.source/backend/tasks/schedule.json"
TASK_PID_FILE = f"/var/apps/fndepot.source/var/.task_pid"
TASK_STOP_FLAG = f"/var/apps/fndepot.source/var/.task_stop"

# 实际任务脚本路径
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TASK_SCRIPT = os.path.join(_BACKEND_DIR, 'tasks', 'fndepot_upgrade_sources.py')
_VENV_PYTHON = os.path.join(_BACKEND_DIR, '.venv', 'bin', 'python3')
if not os.path.exists(_VENV_PYTHON):
    _VENV_PYTHON = sys.executable


def schedule(params: dict, *args, **kwargs):
    """保存定时任务配置到 SCHEDULE_FILE"""
    params = params or {}
    hour = params.get('hour')
    if hour is None:
        raise ValueError("hour is required")

    schedule_dir = os.path.dirname(SCHEDULE_FILE)
    os.makedirs(schedule_dir, exist_ok=True)

    # 读取已有配置，保留 last_executed 字段
    schedule_data = {}
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)
        except Exception:
            pass
    schedule_data['hour'] = hour

    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, ensure_ascii=False)

    logging.info(f"Schedule saved: hour={hour}")
    return {'message': 'ok'}


def get_schedule(params: dict, *args, **kwargs):
    """获取定时任务配置"""
    if not os.path.exists(SCHEDULE_FILE):
        return {'hour': 0, 'notify_upgrade': False}
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
        return {
            'hour': schedule_data.get('hour', 0),
            'notify_upgrade': schedule_data.get('notify_upgrade', False),
        }
    except Exception:
        return {'hour': 0, 'notify_upgrade': False}


def set_notify_upgrade(params: dict, *args, **kwargs):
    """保存系统通知应用更新开关到 SCHEDULE_FILE"""
    params = params or {}
    enabled = params.get('enabled', False)

    schedule_dir = os.path.dirname(SCHEDULE_FILE)
    os.makedirs(schedule_dir, exist_ok=True)

    schedule_data = {}
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)
        except Exception:
            pass
    schedule_data['notify_upgrade'] = enabled

    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, ensure_ascii=False)

    logging.info(f"System notify saved: enabled={enabled}")
    return {'message': 'ok'}


def _is_task_running():
    """检查任务子进程是否还在运行"""
    if not os.path.exists(TASK_PID_FILE):
        return False
    try:
        with open(TASK_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # 进程不存在，清理残留 PID 文件
        try:
            os.remove(TASK_PID_FILE)
        except OSError:
            pass
        return False


def execute(params: dict, *args, **kwargs):
    """立即执行任务，使用 subprocess 在后台运行，CGI 模式下不阻塞"""
    if _is_task_running():
        logging.warning("任务正在执行中，跳过执行")
        return {'message': '任务正在执行中', 'running': True}

    log_dir = os.path.dirname(TASK_LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    if os.path.exists(TASK_STOP_FLAG):
        os.remove(TASK_STOP_FLAG)

    params = params or {}
    trigger_type = params.get('trigger_type', 'manually')
    trigger_time = params.get('trigger_time', None)

    # 读取上次定时执行时间
    last_executed_str = ''
    if trigger_time is not None:
        trigger_time_str = datetime.fromtimestamp(trigger_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
        last_executed_str = f"上次定时执行时间: {trigger_time_str}"

    # 清空日志文件，准备记录新任务日志
    open(TASK_LOG_FILE, 'w').close()
    with open(TASK_LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {datetime.now().strftime('%Z')}- INFO - {'手动执行' if trigger_type == 'manually' else '定时执行'}  {last_executed_str}\n")

    popen_kwargs = {}
    if os.name == 'nt':
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs['start_new_session'] = True

    with open(TASK_LOG_FILE, 'a') as log_file:
        proc = subprocess.Popen(
            [_VENV_PYTHON, '-u', _TASK_SCRIPT, TASK_LOG_FILE],
            stdout=log_file,
            stderr=log_file,
            **popen_kwargs
        )

    with open(TASK_PID_FILE, 'w') as f:
        f.write(str(proc.pid))

    return {'message': '任务已开始执行', 'running': True}


def status(params: dict, *args, **kwargs):
    """返回任务运行状态"""
    return {'running': _is_task_running()}


def stop(params: dict, *args, **kwargs):
    """停止正在执行的任务"""
    if not _is_task_running():
        return {'message': '没有正在执行的任务', 'running': False}

    try:
        with open(TASK_PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 9)
    except Exception as e:
        logging.error(f"停止任务失败: {e}")
    finally:
        # 清理标志文件
        for fpath in (TASK_PID_FILE, TASK_STOP_FLAG):
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    return {'message': '任务已停止', 'running': False}


def log(params: dict, *args, **kwargs):
    """读取任务日志，支持从指定行开始读取（模拟tail -f）"""
    try:
        params = params or {}
        start_line = params.get('start_line', 0)
        try:
            start_line = int(start_line)
        except (ValueError, TypeError):
            start_line = 0

        if not os.path.exists(TASK_LOG_FILE):
            return {'lines': [], 'total_lines': 0, 'next_start': 0}

        with open(TASK_LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)

        if start_line >= total_lines:
            return {'lines': [], 'total_lines': total_lines, 'next_start': total_lines}

        new_lines = all_lines[start_line:]
        new_lines = [line.rstrip('\n').rstrip('\r') for line in new_lines]

        return {
            'lines': new_lines,
            'total_lines': total_lines,
            'next_start': total_lines
        }
    except Exception as e:
        logging.error(f"读取日志异常: {e}")
        return {'lines': [], 'total_lines': 0, 'next_start': 0}


def tick():
    """定时触发检查，由 cmd/main status 调用"""
    if not os.path.exists(SCHEDULE_FILE):
        return

    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)

    if schedule_data.get('notify_upgrade'):
        try:
            with open(APP_LOG_FILE, 'a') as log_file:
                subprocess.Popen(
                    [_VENV_PYTHON, '-u', _TASK_SCRIPT, APP_LOG_FILE, 'notify_upgrade'],
                    stdout=log_file,
                    stderr=log_file,
                    start_new_session=True
                )
        except Exception as e:
            logging.exception(f"系统通知应用更新失败: {e}")

    interval = schedule_data.get('hour')
    if not interval or interval <= 0:
        return

    now = datetime.now()
    current_ts_ms = int(now.timestamp() * 1000)

    last = schedule_data.get('last_executed')
    if last is not None:
        elapsed_hours = (current_ts_ms - last) / 3600000
        if elapsed_hours < interval:
            return

    # 先写执行时间（锁），再执行，避免重复触发
    schedule_data['last_executed'] = current_ts_ms
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, ensure_ascii=False)

    logging.info(f"定时任务触发: interval={interval}h, hour={now.hour}")
    execute({'trigger_type': 'tick', 'trigger_time': last})


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'tick':
        tick()
    else:
        raise Exception("tick 任务需要指定参数 tick")