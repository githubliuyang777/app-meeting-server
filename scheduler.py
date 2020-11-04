import datetime
import json
import logging
import requests
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from meetings.models import Collect, Meeting, User

logger = logging.getLogger('log')


def get_token():
    appid = settings.APP_CONF['appid']
    secret = settings.APP_CONF['secret']
    url = 'https://api.weixin.qq.com/cgi-bin/token?appid={}&secret={}&grant_type=client_credential'.format(appid, secret)
    r = requests.get(url)
    if r.status_code == 200:
        try:
            access_token = r.json()['access_token']
            return access_token
        except KeyError as e:
            logger.error(e)
    else:
        logger.error(r.status_code, r.json())
        logger.error('fail to get access_token,exit.')
        sys.exit(1)


def get_template(openid, template_id, meeting_id, page, topic, time, text):
    page = page + '?id={}'.format(meeting_id)
    content = {
        "touser": openid,
        "template_id": template_id,
        "page": "/pages/meeting/detail?id={}".format(meeting_id),
        "miniprogram_state": "developer",
        "lang": "zh-CN",
        "data": {
            "thing1": {
                "value": topic
            },
            "thing2": {
                "value": time
            },
            "thing3": {
                "value": text
            }
        }
    }
    return content


def send_subscribe_msg():
    logger.info('start to search meetings...')
    # 获取当前日期
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    t1 = datetime.datetime.now().strftime('%H:%M')
    t2 = (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime('%H:%M')
    # 查询当日在t1到t2时段存在的会议
    meetings = Meeting.objects.filter(is_delete=0, date=date, start__gte=t1, start__lte=t2)
    # 若存在符合条件的会议,遍历meetings对每个会议的创建人与收藏者发送订阅消息
    if meetings:
        # 获取access_token
        access_token = get_token()
        # 模板参数
        template_id = 'k1SE-Cy2nwCkRRD7BBYKFQInwDXNs1sZuMcqECJgBgg'
        page = '/pages/meeting/detail'
        text = '会议即将开始'
        for meeting in meetings:
            topic = meeting.topic
            start_time = meeting.start
            meeting_id = meeting.id
            time = date + ' ' + start_time
            mid = meeting.mid
            creater_id = meeting.user_id
            creater_openid = User.objects.get(id=creater_id).openid
            send_to_list = [creater_openid]
            # 查询该会议的收藏
            collections = Collect.objects.filter(meeting_id=meeting.id)
            # 若存在collections,遍历collections将openid添加入send_to_list
            if collections:
                for collection in collections:
                    user_id = collection.user_id
                    openid = User.objects.get(id=user_id).openid
                    send_to_list.append(openid)
                # 发送列表去重
                send_to_list = list(set(send_to_list))
            else:
                logger.info('the meeting {} had not been added to Favorites'.format(mid))
            for openid in send_to_list:
                # 获取模板
                content = get_template(openid, template_id, meeting_id, page, topic, time, text)
                # 发送订阅消息
                url = 'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={}'.format(
                    access_token)
                r = requests.post(url, json.dumps(content))
                if r.status_code != 200:
                    logger.error(r.status_code, r.json())
                else:
                    if r.json()['errCode'] != 0:
                        logger.warning(r.json()['errCode'], r.json()['errMsg'])
            logger.info('meeting {} subscription message sent.'.format(mid))
    else:
        logger.info('no meeting found, skip meeting notify.')


def run_task():
    # 服务启动即开始任务
    send_subscribe_msg()
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(send_subscribe_msg, 'cron', hour='0-23', minute='*/10')
        scheduler.start()
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    run_task()