"""
Auto BaiduYun uplaod script

Usage:
    python auto_baiduyun_upload.py -f filepath

Optional arguments:
    -h, --help  show help doc
    -f, --file  select upload file
"""

import os
import sys
import getopt
import psutil
import time
from subprocess import Popen, PIPE
from pynput import keyboard
from log import logger


# 参数解析部分
def arg_check(argv):
    try:
        options, args = getopt.getopt(argv, 'hf:', ['help', 'file='])
    except getopt.GetoptError:
        print(__doc__)
        sys.exit()
    if not options:
        print(__doc__)
        sys.exit()
    for name, value in options:
        if name in ['-h', '--help']:
            print(__doc__)
            sys.exit()
        if name in ['-f', '--file']:
            file_path = value
            return file_path


# 检查进程pid
def process_pid(process_name):
    pids_list = psutil.pids()
    for pid in pids_list:
        if psutil.Process(pid).name() == process_name:
            return pid
    return -1


# 获取进程路径
def process_path(pid):
    p = psutil.Process(pid)
    return p.exe()


# 键盘按键输入
def kb_press(*keys):
    kb = keyboard.Controller()
    for key in keys:
        kb.press(key)
    for key in keys:
        kb.release(key)
    return


# 键盘文本输入
def kb_type(text):
    kb = keyboard.Controller()
    kb.type(text)
    return


def upload_opr(file_path):
    # 确认文件存在
    if not os.path.exists(file_path):
        logger.error('ERROR: file not find.')
        return

    # 检查百度云网盘主程序运行状态
    baiduyun_pid = process_pid('BaiduNetdisk.exe')
    if baiduyun_pid == -1:
        logger.error('ERROR: 百度云网盘主程序未运行.')
        return
    baiduyun_path = process_path(baiduyun_pid)

    logger.info(f'模拟上传文件操作, file: {file_path}')
    # 呼出资源管理器并等待启动, 选中指定文件并复制
    cmd = fr'explorer /select,{file_path}'
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    p.wait()
    time.sleep(3)
    kb_press(keyboard.Key.ctrl, 'c')
    time.sleep(1)
    kb_press(keyboard.Key.alt, keyboard.Key.f4)

    # 呼出百度云管家窗口
    cmd = fr'{baiduyun_path}'
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    p.wait()

    # 直接粘贴(上传)
    time.sleep(3)
    kb_press(keyboard.Key.ctrl, 'v')
    time.sleep(1)
    kb_press(keyboard.Key.alt, keyboard.Key.f4)


__all__ = [
    'upload_opr',
]


if __name__ == '__main__':
    upload_opr(file_path=arg_check(sys.argv[1:]))
