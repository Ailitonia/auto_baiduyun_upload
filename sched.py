import asyncio
from auto_baiduyun_upload import upload_opr
from config import RECORD_FILE_PATH
from log import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from util import query_live_sub_list, get_live_info, all_sub_file, check_new_file, text_sha1

live_status = {}
scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    # hour=None,
    minute='*/10',
    # second='*/10',
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=30
)
async def main_job():
    global live_status

    for sub_id in query_live_sub_list():
        try:
            # 获取直播间信息
            live_info = await get_live_info(sub_id)
        except Exception as get_info_err:
            logger.warning(f'check_live, ERROR: {get_info_err}, sub_id:  {sub_id}.')
            continue

        # 检查直播状态变化
        if live_info['status'] != live_status[sub_id]:
            # 下播了, 执行模拟上传文件
            if live_info['status'] in [0, 2]:
                files_list = all_sub_file(sub_id=sub_id, path=RECORD_FILE_PATH)
                for file_name, file_path in files_list:
                    if check_new_file(text_sha1(file_name)):
                        upload_opr(file_path)
                # 更新直播间状态
                live_status[sub_id] = live_info['status']
            # 开播了
            else:
                # 更新直播间状态
                live_status[sub_id] = live_info['status']


async def _init():
    global live_status
    for room_id in query_live_sub_list():
        try:
            # 获取直播间信息
            live_info = await get_live_info(room_id)
            # 直播状态放入live_status全局变量中
            live_status[room_id] = int(live_info['status'])
        except Exception as e:
            logger.error(f'初始化直播间状态列表时发生了错误: {e}, room_id: {room_id}')
            continue
    logger.info(f'完成直播间状态列表初始化')


def start_scheduler():
    if not scheduler.running:
        asyncio.gather(_init())
        scheduler.configure({'apscheduler.timezone': 'Asia/Shanghai'})
        scheduler.start()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            logger.info(f'用户终止了任务')


__all__ = [
    'start_scheduler'
]

if __name__ == '__main__':
    start_scheduler()
