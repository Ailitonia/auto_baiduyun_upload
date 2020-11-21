import os
import re
import hashlib
import aiohttp
from asyncio.exceptions import TimeoutError
from log import logger
from datetime import datetime
from db import *
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


LIVE_API_URL = 'https://api.live.bilibili.com/room/v1/Room/get_info'
USER_INFO_API_URL = 'https://api.bilibili.com/x/space/acc/info'
LIVE_URL = 'https://live.bilibili.com/'


async def fetch_json(url: str, paras: dict) -> dict:
    timeout = aiohttp.ClientTimeout(total=10)
    err_count = 0
    while err_count < 3:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, params=paras, headers=headers, timeout=timeout) as resp:
                    __json = await resp.json()
            return __json
        except TimeoutError:
            print(f'fetch WARNING: TimeoutError. Occurred in try {err_count + 1} using paras: {paras}')
        except Exception as e:
            print(f'fetch WARNING: {e}. Occurred in try {err_count + 1} using paras: {paras}')
        finally:
            err_count += 1
    else:
        print(f'fetch ERROR: errors exceeded {err_count}, using paras: {paras}')
        return {'error': 'error'}


# 获取直播间信息
async def get_live_info(room_id) -> dict:
    url = LIVE_API_URL
    payload = {'id': room_id}
    live_info = await fetch_json(url=url, paras=payload)
    if live_info['code'] != 0:
        return dict({'status': 'error'})
    return dict({'status': live_info['data']['live_status'], 'url': LIVE_URL + str(room_id),
                 'title': live_info['data']['title'], 'time': live_info['data']['live_time'],
                 'uid': live_info['data']['uid']})


# 根据用户uid获取用户信息
async def get_user_info(user_id) -> dict:
    url = USER_INFO_API_URL
    payload = {'mid': user_id}
    user_info = await fetch_json(url=url, paras=payload)
    if user_info['code'] != 0:
        return dict({'status': 'error'})
    return dict({'status': user_info['code'], 'name': user_info['data']['name']})


# 返回所有直播间房间号的列表
def query_live_sub_list() -> list:
    result = []
    for res in DBSESSION.query(Subscription.sub_id).order_by(Subscription.id).all():
        result.append(res[0])
    return result


# 向订阅表中添加(更新)直播间订阅
def add_live_sub(sub_id, up_name) -> bool:
    sub_id = int(sub_id)
    up_name = str(up_name)
    # 若存在则更新订阅表中up名称
    try:
        exist_sub = DBSESSION.query(Subscription).filter(Subscription.sub_id == sub_id).one()
        exist_sub.up_name = up_name
        exist_sub.updated_at = datetime.now()
        DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则添加新订阅
        try:
            new_sub = Subscription(sub_id=sub_id, up_name=up_name, created_at=datetime.now())
            DBSESSION.add(new_sub)
            DBSESSION.commit()
            return True
        except Exception as e:
            DBSESSION.rollback()
            logger.error(f'add_live_sub, DBSESSION ERROR: {e}.')
            return False
    except MultipleResultsFound:
        logger.warning(f'add_live_sub, MultipleResultsFound, sub_id: {sub_id}.')
        return False
    except Exception as e:
        DBSESSION.rollback()
        logger.error(f'add_live_sub, DBSESSION ERROR: {e}.')
        return False


# 向文件表中添加(更新)文件信息
def add_file(file_name_hash, sub_id) -> bool:
    file_name_hash = str(file_name_hash)
    sub_id = int(sub_id)

    # 若存在则pass
    try:
        DBSESSION.query(Files).filter(Files.file_name_hash == file_name_hash).one()
        return True
    except NoResultFound:
        # 不存在则添加
        try:
            new_sub = Files(file_name_hash=file_name_hash, sub_id=sub_id, created_at=datetime.now())
            DBSESSION.add(new_sub)
            DBSESSION.commit()
            return True
        except Exception as e:
            DBSESSION.rollback()
            logger.error(f'add_file, DBSESSION ERROR: {e}.')
            return False
    except MultipleResultsFound:
        logger.warning(f'add_file, MultipleResultsFound, file_name_hash: {file_name_hash}.')
        return False
    except Exception as e:
        DBSESSION.rollback()
        logger.error(f'add_file, DBSESSION ERROR: {e}.')
        return False


# 检查该文件是否已经存在
def check_new_file(file_name_hash: str) -> bool:
    try:
        DBSESSION.query(Files).filter(Files.file_name_hash == file_name_hash).one()
        return False
    except NoResultFound:
        return True
    except Exception:
        return False


# 通过房间号添加直播间
async def new_live_sub(sub_id) -> bool:
    live_info = await get_live_info(sub_id)
    if live_info['status'] == 'error':
        logger.error(f'new_live_sub: 没有找到该房间号: {sub_id} 对应的直播间')
        return False
    up_info = await get_user_info(live_info['uid'])
    up_name = up_info['name']

    is_success = add_live_sub(sub_id=sub_id, up_name=up_name)
    if not is_success:
        logger.error(f'new_live_sub: 添加直播间信息数据库操作失败.')
        return False
    else:
        logger.info(f'new_live_sub: 已添加直播间: {sub_id}.')
        return True


# 根据房间号列出对应录播文件列表
def all_sub_file(sub_id, path) -> list:
    file_name_p = rf'^录制-{sub_id}-'
    file_path_list = []
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if re.match(file_name_p, file_name):
                file_path_list.append((file_name, os.path.join(root, file_name)))
    return file_path_list


# 计算字符串sha1
def text_sha1(text: str) -> str:
    sha1 = hashlib.sha1()
    sha1.update(text.encode('utf-8'))
    sha1_sum = sha1.hexdigest()
    return sha1_sum


if __name__ == '__main__':
    print(all_sub_file(21641569, 'Z:\\BililiveRecorder'))
