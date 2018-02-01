#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: wx_client.py
@time: 2017-12-27 17:57
"""

from __future__ import print_function
from __future__ import unicode_literals

import json
import os
import random
import re
import sys
import time
from HTMLParser import HTMLParser
from functools import wraps

import xmltodict

from config import current_config
from tools.format import format_info, print_info, output_line
from tools.session import session_obj

BASE_DIR = current_config.BASE_DIR
REQUESTS_TIME_OUT = current_config.REQUESTS_TIME_OUT

html_parser = HTMLParser()


def catch_keyboard_interrupt(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print('\n强制退出')

    return wrapper


class WXClient(object):
    cookies = {}

    headers = {
        # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0'
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/63.0.3239.84 Safari/537.36'
    }

    appid = 'wx782c26e4c19acffb'
    lang = 'zh_CN'
    qr_img_name = 'qrcode.jpg'
    uuid = ''

    redirect_uri = ''
    base_uri = ''

    skey = ''
    wxsid = ''
    wxuin = ''
    pass_ticket = ''

    synckey = ''
    SyncKey = {}

    client_info = {}
    client_contact = {}
    client_group_contact = {}
    client_group_tmp_contact = {}

    login_user_nick_name = ''
    login_user_sex = 0

    sync_host = 'webpush.wx.qq.com'

    def __init__(self, debug=False):
        self.debug = debug
        self.s = session_obj
        self.device_id = self._get_device_id()

    @staticmethod
    def _get_device_id():
        return 'e' + repr(random.random())[2:17]
        # return 'e%15d' % (random.random()*(10**15))

    @staticmethod
    def _get_tc():
        tc = str('%13d' % (time.time() * 1000))
        return tc

    @staticmethod
    def _get_r():
        return int(time.time())

    @staticmethod
    def _parse_qr_code_uuid(html_body):
        """
        获取二维码uuid
        :param html_body:
        :return:
        """
        rule = ur'window.QRLogin.code = 200; window.QRLogin.uuid = "(.*?)";'
        res_list = re.compile(rule, re.S).findall(html_body)
        return ''.join(res_list)

    @staticmethod
    def _parse_code(html_body):
        """
        获取状态码code
        :param html_body:
        :return:
        """
        rule = ur'window.code=(\d+);'
        res_list = re.compile(rule, re.S).findall(html_body)
        return ''.join(res_list)

    @staticmethod
    def _parse_redirect_url(html_body):
        """
        获取跳转链接
        :param html_body:
        :return:
        """
        rule = ur'window.redirect_uri="(.*?)";'
        res_list = re.compile(rule, re.S).findall(html_body)
        return ''.join(res_list)

    @staticmethod
    def _parse_sync_check(html_body):
        pm = re.search(ur'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', html_body)
        retcode = pm.group(1)
        selector = pm.group(2)
        # print(retcode, selector)
        return retcode, selector

    @staticmethod
    def _xml_to_dict(xml_body):
        """
        将xml转为dict
        """
        xml_dict = xmltodict.parse(xml_body)
        # print(json.dumps(xml_dict, indent=4, ensure_ascii=False))
        return xml_dict

    def _save_img(self, res):
        with open(self.qr_img_name, b'wb') as f:
            for chunk in res.iter_content(1024):
                f.write(chunk)

    def _open_img(self):
        # linux, darwin
        if sys.platform.lower() == "linux":
            os.system("xdg-open %s &" % self.qr_img_name)
        else:
            os.system('open %s &' % self.qr_img_name)

    @staticmethod
    def _replace_html(input_html, reg_expression=r'', replace_text=''):
        """
        正则替换
        :param input_html:
        :param reg_expression:
        :param replace_text:
        :return:
        """
        p = re.compile(reg_expression, re.I)  # .*后面跟上? 非贪婪匹配 re.I大小写不敏感
        output_html = p.sub(replace_text, input_html)
        return output_html

    @staticmethod
    def _strip_html(input_html):
        """
        去除html标签
        :param input_html:
        :return:
        """
        # p = re.compile('<[^>]+>')
        p = re.compile(r'<.*?>')  # .*后面跟上? 非贪婪匹配
        return p.sub("", input_html)

    @staticmethod
    def _format_time(tc=0):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(tc) or time.time()))

    def get_uuid(self):
        """
        window.QRLogin.code = 200; window.QRLogin.uuid = "AcsD_03fLw==";
        :return:
        """
        url = 'https://login.wx.qq.com/jslogin'
        request_headers = self.headers
        params = {
            'appid': self.appid,
            # 'redirect_uri': 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun': 'new',
            'lang': self.lang,
            '_': self._get_tc(),
        }
        res = self.s.get(url, params=params, headers=request_headers, timeout=REQUESTS_TIME_OUT)
        # print(res.content)
        self.uuid = self._parse_qr_code_uuid(res.content)

    def get_qr_code(self):
        url = 'https://login.weixin.qq.com/qrcode/%s' % self.uuid
        request_headers = self.headers
        res = self.s.get(url, headers=request_headers, timeout=REQUESTS_TIME_OUT, stream=True)
        self._save_img(res)
        self._open_img()

    def wait_for_login(self, tip=1):
        """
        window.code=200;
        window.redirect_uri="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AVKXV1c32_ZF4BkiXQDffPZv@qrticket_0&uuid=AcsD_03fLw==&lang=zh_CN&scan=1514301218";
        :return:
        """
        time.sleep(tip)
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login'
        request_headers = self.headers
        params = {
            'tip': tip,
            'uuid': self.uuid,
            '_': self._get_tc(),
        }
        data = self.s.get(url, params=params, headers=request_headers, timeout=REQUESTS_TIME_OUT).content
        if not data:
            return False
        code = self._parse_code(data)

        if code == '201':
            return True
        elif code == '200':
            r_uri = self._parse_redirect_url(data)
            r_uri += '&fun=new'
            self.redirect_uri = r_uri
            self.base_uri = r_uri[:r_uri.rfind('/')]
            # print(self.redirect_uri)
            # print(self.base_uri)
            print('[登陆成功]')
            return True
        elif code == '408':
            print('[登陆超时]')
        else:
            print('[登陆异常]')
        return False

    def login(self):
        """
        <error>
            <ret>0</ret>
            <message></message>
            <skey>@crypt_45c6ee27_bd55a6ef749b2011bc7a14dc59572f2e</skey>
            <wxsid>4Gg+xICjRp90bOhx</wxsid>
            <wxuin>1093017365</wxuin>
            <pass_ticket>Blm%2BnQqzncrNHsxm2sErzrcCSg9dn3LK5Cgry0Q8yJcg%2BFaHQ0IuiPD8KmeWSA7Y</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
        :return:
        """
        request_headers = self.headers

        res = self.s.get(self.redirect_uri, headers=request_headers, timeout=REQUESTS_TIME_OUT)
        data = self._xml_to_dict(res.content)
        self.skey = data['error']['skey']
        self.wxsid = data['error']['wxsid']
        self.wxuin = data['error']['wxuin']
        self.pass_ticket = data['error']['pass_ticket']

    def web_wx_init(self):
        request_headers = self.headers
        request_headers.update({'Content-Type': 'application/json;charset=utf-8'})
        url = self.base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, self._get_r())
        payload = {
            'BaseRequest': {
                'Uin': self.wxuin,
                'Sid': self.wxsid,
                'Skey': self.skey,
                'DeviceID': self.device_id,
            }
        }

        self.client_info = json.loads(self.s.post(url, headers=request_headers, json=payload).content)
        # print('web_wx_init')
        # print(json.dumps(self.client_info, indent=4, ensure_ascii=False))
        with open(os.path.join(BASE_DIR, 'contacts/client_info.json'), b'wb') as f:
            f.write(json.dumps(self.client_info, indent=4))

        self.SyncKey = self.client_info['SyncKey']
        self.synckey = '|'.join(['%s_%s' % (i['Key'], i['Val']) for i in self.client_info['SyncKey']['List']])

    def web_wx_status_notify(self):
        """
        {
            "BaseResponse": {
                "Ret": 0,
                "ErrMsg": ""
            },
            "MsgID": "6745763515704201399"
        }

        :return:
        """
        request_headers = self.headers
        request_headers.update({'Content-Type': 'application/json;charset=utf-8'})
        url = self.base_uri + '/webwxstatusnotify?lang=%s&pass_ticket=%s' % (self.lang, self.pass_ticket)
        payload = {
            'BaseRequest': {
                'Uin': self.wxuin,
                'Sid': self.wxsid,
                'Skey': self.skey,
                'DeviceID': self.device_id,
            },
            "Code": 3,
            "FromUserName": self.client_info['User']['UserName'],
            "ToUserName": self.client_info['User']['UserName'],
            "ClientMsgId": self._get_tc()
        }
        # print('web_wx_status_notify')
        res = self.s.post(url, headers=request_headers, json=payload)
        if res.status_code == 200:
            # print(res.json())
            pass

    def web_wx_get_contact(self):
        """
        获取联系人
        :return:
        """
        url = self.base_uri + '/webwxgetcontact'
        request_headers = self.headers
        params = {
            'pass_ticket': self.pass_ticket,
            'r': self._get_r(),
            'seq': '0',
            'skey': self.skey,
        }
        self.client_contact = json.loads(
            self.s.get(url, params=params, headers=request_headers, timeout=REQUESTS_TIME_OUT).content)
        # print('web_wx_get_contact')
        # print(json.dumps(self.client_contact, indent=4, ensure_ascii=False))
        with open(os.path.join(BASE_DIR, 'contacts/client_contact.json'), b'wb') as f:
            f.write(json.dumps(self.client_contact, indent=4))

    def web_wx_get_group_contact(self):
        """
        批量获取扩展联系方式（适用获取群员信息）
        注意:
            1、只有保存到通讯录的群聊才能获取群员详细信息
            2、保存到通讯录、置顶两个都勾选后，会重复显示
        :return:
        """
        url = self.base_uri + '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (self._get_tc(), self.pass_ticket)
        # print(url)
        request_headers = self.headers
        request_headers.update({'Content-Type': 'application/json;charset=utf-8'})

        group_list = [{'UserName': member['UserName'], 'EncryChatRoomId': member['EncryChatRoomId']} for member in
                      self.client_contact['MemberList'] if member['UserName'].startswith('@@')]

        # print('group_list')
        # print(group_list)

        payload = {
            'BaseRequest': {
                'Uin': self.wxuin,
                'Sid': self.wxsid,
                'Skey': self.skey,
                'DeviceID': self.device_id,
            },
            'Count': len(group_list),
            'List': group_list
        }
        # print('web_wx_get_group_contact payload:')
        # print(payload)
        self.client_group_contact = json.loads(
            self.s.post(url, json=payload, headers=request_headers, timeout=REQUESTS_TIME_OUT).content)
        # print('web_wx_get_group_contact')
        # print(json.dumps(self.client_group_contact, indent=4, ensure_ascii=False))
        with open(os.path.join(BASE_DIR, 'contacts/client_group_contact.json'), b'wb') as f:
            f.write(json.dumps(self.client_group_contact, indent=4))

    def web_wx_get_group_tmp_contact(self):
        """
        批量获取扩展联系方式（适用获取群聊、临时群组成员信息）
        :return:
        """
        url = self.base_uri + '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (self._get_tc(), self.pass_ticket)
        # print(url)
        request_headers = self.headers
        request_headers.update({'Content-Type': 'application/json;charset=utf-8'})

        self.client_group_tmp_contact = {}

        for group_info in self.client_info['ContactList']:

            if not group_info['UserName'].startswith('@@') or not group_info['MemberList']:
                continue
            member_list = group_info['MemberList']
            if len(member_list) <= 50:
                group_list = [{'UserName': member['UserName'], 'EncryChatRoomId': group_info['UserName']} for member in
                              member_list]

                payload = {
                    'BaseRequest': {
                        'Uin': self.wxuin,
                        'Sid': self.wxsid,
                        'Skey': self.skey,
                        'DeviceID': self.device_id,
                    },
                    'Count': len(group_list),
                    'List': group_list
                }
                self.client_group_tmp_contact[group_info['UserName']] = json.loads(
                    self.s.post(url, json=payload, headers=request_headers, timeout=REQUESTS_TIME_OUT).content)
            else:
                c = 0
                while 1:
                    if c * 50 > len(member_list):
                        break
                    list_start = c * 50
                    c += 1
                    list_end = c * 50
                    group_list = [{'UserName': member['UserName'], 'EncryChatRoomId': group_info['UserName']} for member
                                  in
                                  member_list[list_start:list_end]]

                    payload = {
                        'BaseRequest': {
                            'Uin': self.wxuin,
                            'Sid': self.wxsid,
                            'Skey': self.skey,
                            'DeviceID': self.device_id,
                        },
                        'Count': len(group_list),
                        'List': group_list
                    }
                    result = json.loads(
                        self.s.post(url, json=payload, headers=request_headers, timeout=REQUESTS_TIME_OUT).content)
                    if group_info['UserName'] not in self.client_group_tmp_contact:
                        self.client_group_tmp_contact[group_info['UserName']] = result
                    else:
                        self.client_group_tmp_contact[group_info['UserName']]['Count'] += result['Count']
                        self.client_group_tmp_contact[group_info['UserName']]['ContactList'].extend(result['ContactList'])

        # print('web_wx_get_group_tmp_contact')
        # print(json.dumps(self.client_group_tmp_contact, indent=4, ensure_ascii=False))
        with open(os.path.join(BASE_DIR, 'contacts/client_group_tmp_contact.json'), b'wb') as f:
            f.write(json.dumps(self.client_group_tmp_contact, indent=4))

    def sync_check(self):
        """
        同步检查
        :return:
        """
        url = 'https://' + self.sync_host + '/cgi-bin/mmwebwx-bin/synccheck'
        # url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck'
        request_headers = self.headers

        params = {
            'r': self._get_tc(),
            'skey': self.skey,
            'sid': self.wxsid,
            'uin': self.wxuin,
            'deviceid': self.device_id,
            'synckey': self.synckey,
            '_': self._get_tc(),
        }

        check_res = self.s.get(url, params=params, headers=request_headers, timeout=REQUESTS_TIME_OUT)
        if not check_res.content:
            return False

        return self._parse_sync_check(check_res.content)

    def web_wx_sync(self):
        url = self.base_uri + '/webwxsync?sid=%s&skey=%s&pass_ticket=%s' % (self.wxsid, self.skey, self.pass_ticket)
        request_headers = self.headers
        request_headers.update({'Content-Type': 'application/json;charset=utf-8'})
        payload = {
            'BaseRequest': {
                'Uin': self.wxuin,
                'Sid': self.wxsid,
                'Skey': self.skey,
                'DeviceID': self.device_id,
            },
            'SyncKey': self.SyncKey,
            'rr': self._get_r()
        }

        web_wx_sync_info = json.loads(
            self.s.post(url, json=payload, headers=request_headers, timeout=REQUESTS_TIME_OUT).content)
        # print(json.dumps(web_wx_sync_info, indent=4, ensure_ascii=False))

        self.SyncKey = web_wx_sync_info['SyncKey']
        self.synckey = '|'.join(['%s_%s' % (i['Key'], i['Val']) for i in web_wx_sync_info['SyncKey']['List']])

        self.handle_msg(web_wx_sync_info)

    def handle_msg(self, data):
        msg_count = data['AddMsgCount']
        if msg_count == 0:
            return False
        for msg in data['AddMsgList']:
            msg_id = msg['MsgId']
            from_user_name = msg['FromUserName']
            to_user_name = msg['ToUserName']
            msg_type = msg['MsgType']
            sub_msg_type = msg['SubMsgType']
            status = msg['Status']
            content = html_parser.unescape(msg['Content'])
            create_time = msg['CreateTime']
            # new_msg_id = msg['NewMsgId']
            status_notify_code = msg['StatusNotifyCode']

            # debug 模式支持消息调试
            if self.debug:
                print(msg)  # debug

            # 消息类型
            msg_type_map = {
                1: '文字',
                3: '图片',
                34: '语音',
                47: '表情',
                62: '视频',
            }
            # 位置信息
            if msg_type == 1 and sub_msg_type == 48:
                # 群组消息 - 接收
                if from_user_name.startswith('@@') and ':<br/>' in content:
                    to_user_name = content.split(':<br/>', 1)[0]
                    group_info, member_info = self.get_group_member(from_user_name, to_user_name)
                    content = content.split(':<br/>', 1)[1]
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 接收')

                # 群组消息 - 发送
                elif to_user_name.startswith('@@'):
                    group_info, member_info = self.get_group_member(to_user_name, from_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 发送')

                # 个人消息
                else:
                    from_user_name_info = self.get_contact_member(from_user_name)
                    to_user_name_info = self.get_contact_member(to_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来自', from_user_name_info),
                        format_info('消息发至', to_user_name_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    status_msg = '接收' if self.client_info['User']['NickName'] == to_user_name_info else '发送'
                    print_info(contents, '个人消息 - %s' % status_msg)
            if msg_type in msg_type_map:
                # 群组消息 - 接收
                if from_user_name.startswith('@@') and ':<br/>' in content:
                    to_user_name = content.split(':<br/>', 1)[0]
                    group_info, member_info = self.get_group_member(from_user_name, to_user_name)
                    content = content.split(':<br/>', 1)[1]
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 接收')

                # 群组消息 - 发送
                elif to_user_name.startswith('@@'):
                    group_info, member_info = self.get_group_member(to_user_name, from_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 发送')

                # 个人消息
                else:
                    from_user_name_info = self.get_contact_member(from_user_name)
                    to_user_name_info = self.get_contact_member(to_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', msg_type_map[msg_type]),
                        format_info('消息来自', from_user_name_info),
                        format_info('消息发至', to_user_name_info),
                        format_info('消息内容', content, False),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    status_msg = '接收' if self.client_info['User']['NickName'] == to_user_name_info else '发送'
                    print_info(contents, '个人消息 - %s' % status_msg)

            # 微信名片
            elif msg_type == 42:
                msg_content = self._xml_to_dict(self._replace_html(content, '<br/>', '\n').strip())
                sex_map = {
                    '1': '男',
                    '2': '女',
                }

                recommend_show = '\n'.join([
                    '\t昵称: %s' % msg_content['msg']['@nickname'],
                    '\t微信: %s' % msg_content['msg']['@username'],
                    '\t地区: %s %s' % (msg_content['msg']['@province'], msg_content['msg']['@city']),
                    '\t性别: %s' % sex_map.get(msg_content['msg']['@sex'], '-')
                ])

                # 群组消息 - 接收
                if from_user_name.startswith('@@') and ':<br/>' in content:
                    to_user_name = content.split(':<br/>', 1)[0]
                    group_info, member_info = self.get_group_member(from_user_name, to_user_name)

                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信名片'),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', ''),
                        recommend_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 接收')

                # 群组消息 - 发送
                elif to_user_name.startswith('@@'):
                    # print(to_user_name, from_user_name)
                    group_info, member_info = self.get_group_member(to_user_name, from_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信名片'),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', ''),
                        recommend_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 发送')

                # 个人消息
                else:
                    from_user_name_info = self.get_contact_member(from_user_name)
                    to_user_name_info = self.get_contact_member(to_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信名片'),
                        format_info('消息来自', from_user_name_info),
                        format_info('消息发至', to_user_name_info),
                        format_info('消息内容', ''),
                        recommend_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    status_msg = '接收' if self.client_info['User']['NickName'] == to_user_name_info else '发送'
                    print_info(contents, '个人消息 - %s' % status_msg)

            # 微信分享/推送
            elif msg_type == 49:
                # print(msg)
                app_msg_type = {5: '链接', 3: '音乐', 7: '微博', 33: '小程序'}.get(msg['AppMsgType'], '-')

                # 群组消息 - 接收
                if from_user_name.startswith('@@') and ':<br/>' in content:

                    to_user_name = content.split(':<br/>', 1)[0]
                    group_info, member_info = self.get_group_member(from_user_name, to_user_name)
                    content = content.split(':<br/>', 1)[1]

                    msg_content = self._xml_to_dict(self._replace_html(content, '<br/>', '\n').strip())
                    # print(msg_content)

                    shared_show = '\n'.join([
                        '\t标题: %s' % msg_content['msg']['appmsg']['title'],
                        '\t描述: %s' % msg_content['msg']['appmsg']['des'],
                        '\t链接: %s' % msg_content['msg']['appmsg']['url'],
                        '\t来自: %s [%s]' % (
                            # msg_content['msg']['appmsg']['sourcedisplayname'],
                            # msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['appinfo']['appname'] or msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['fromusername'],
                        ),
                    ])

                    # to_user_name = content.split(':<br/>', 1)[0]
                    # group_info, member_info = self.get_group_member(from_user_name, to_user_name)

                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信分享 %s' % app_msg_type),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', ''),
                        shared_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 接收')

                # 群组消息 - 发送
                elif to_user_name.startswith('@@'):
                    group_info, member_info = self.get_group_member(to_user_name, from_user_name)

                    msg_content = self._xml_to_dict(self._replace_html(content, '<br/>', '\n').strip())
                    # print(msg_content)

                    shared_show = '\n'.join([
                        '\t标题: %s' % msg_content['msg']['appmsg']['title'],
                        '\t描述: %s' % msg_content['msg']['appmsg']['des'],
                        '\t链接: %s' % msg_content['msg']['appmsg']['url'],
                        '\t来自: %s [%s]' % (
                            # msg_content['msg']['appmsg']['sourcedisplayname'],
                            # msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['appinfo']['appname'] or msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['fromusername'],
                        ),
                    ])

                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信分享 %s' % app_msg_type),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', ''),
                        shared_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '群组消息 - 发送')

                # 个人消息
                else:
                    msg_content = self._xml_to_dict(self._replace_html(content, '<br/>', '\n').strip())
                    # print(msg_content)

                    shared_show = '\n'.join([
                        '\t标题: %s' % msg_content['msg']['appmsg']['title'],
                        '\t描述: %s' % msg_content['msg']['appmsg']['des'],
                        '\t链接: %s' % msg_content['msg']['appmsg']['url'],
                        '\t来自: %s [%s]' % (
                            # msg_content['msg']['appmsg']['sourcedisplayname'],
                            # msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['appinfo']['appname'] or msg_content['msg']['appmsg']['sourceusername'],
                            msg_content['msg']['fromusername'] or '公号推送',
                        ),
                    ])

                    from_user_name_info = self.get_contact_member(from_user_name)
                    to_user_name_info = self.get_contact_member(to_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '微信分享 %s' % app_msg_type),
                        format_info('消息来自', from_user_name_info),
                        format_info('消息发至', to_user_name_info),
                        format_info('消息内容', ''),
                        shared_show,
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    status_msg = '接收' if self.client_info['User']['NickName'] == to_user_name_info else '发送'
                    print_info(contents, '个人消息 - %s' % status_msg)

            # 状态通知(可以忽略)
            elif msg_type == 51:
                # 群组消息
                op_map = {2: '打开', 4: '展示', 5: '关闭'}

                if to_user_name.startswith('@@'):
                    group_info, member_info = self.get_group_member(to_user_name, from_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '通知'),
                        format_info('消息来源', group_info),
                        format_info('消息来自', member_info),
                        format_info('消息内容', '手机%s聊天窗口' % op_map.get(status_notify_code, '操作')),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '状态通知')
                else:
                    to_user_name_info = self.get_contact_member(to_user_name)
                    from_user_name_info = self.get_contact_member(from_user_name)
                    contents = [
                        format_info('消息编号', msg_id),
                        format_info('消息类型', '通知'),
                        format_info('消息来源', to_user_name_info),
                        format_info('消息来自', from_user_name_info),
                        format_info('消息内容', '手机%s聊天窗口' % op_map.get(status_notify_code, '操作')),
                        format_info('消息时间', self._format_time(create_time)),
                    ]
                    print_info(contents, '状态通知')

            # 通知消息
            elif msg_type == 10000:
                # print(msg)
                if status == 3:
                    # 红包通知
                    # 群组消息 - 接收
                    if from_user_name.startswith('@@') and ':<br/>' in content:
                        to_user_name = content.split(':<br/>', 1)[0]
                        group_info, member_info = self.get_group_member(from_user_name, to_user_name)
                        contents = [
                            format_info('消息编号', msg_id),
                            format_info('消息类型', '红包'),
                            format_info('消息来源', group_info),
                            format_info('消息来自', member_info),
                            format_info('消息内容', '收到红包，请在手机上查看'),
                            format_info('消息时间', self._format_time(create_time)),
                        ]
                        print_info(contents, '群组消息 - 接收')

                    # 群组消息 - 发送
                    elif to_user_name.startswith('@@'):
                        # print(to_user_name, from_user_name)
                        group_info, member_info = self.get_group_member(to_user_name, from_user_name)
                        contents = [
                            format_info('消息编号', msg_id),
                            format_info('消息类型', '红包'),
                            format_info('消息来源', group_info),
                            format_info('消息来自', member_info),
                            format_info('消息内容', '发送红包，请在手机上查看'),
                            format_info('消息时间', self._format_time(create_time)),
                        ]
                        print_info(contents, '群组消息 - 发送')

                    # 个人消息
                    else:
                        from_user_name_info = self.get_contact_member(from_user_name)
                        to_user_name_info = self.get_contact_member(to_user_name)

                        status_msg = '接收' if self.client_info['User']['NickName'] == to_user_name_info else '发送'

                        contents = [
                            format_info('消息编号', msg_id),
                            format_info('消息类型', '红包'),
                            format_info('消息来自', from_user_name_info),
                            format_info('消息发至', to_user_name_info),
                            format_info('消息内容', '%s红包，请在手机上查看' % status_msg),
                            format_info('消息时间', self._format_time(create_time)),
                        ]

                        print_info(contents, '个人消息 - %s' % status_msg)

                if status == 4:
                    # 邀请通知
                    # 群组消息 - 邀请通知
                    if from_user_name.startswith('@@'):
                        group_info, member_info = self.get_group_member(from_user_name, to_user_name)
                        contents = [
                            format_info('消息编号', msg_id),
                            format_info('消息类型', '邀请通知'),
                            format_info('消息来源', group_info),
                            format_info('消息来自', member_info),
                            format_info('消息内容', content),
                            format_info('消息时间', self._format_time(create_time)),
                        ]
                        print_info(contents, '群组消息 - 邀请通知')

            # 撤回消息
            elif msg_type == 10002:
                print(msg)
                contents = [
                    format_info('消息编号', msg_id),
                    format_info('消息来源', from_user_name),
                    format_info('消息类型', msg_type),
                    format_info('消息来自', from_user_name),
                    format_info('消息内容', '撤回消息'),
                    format_info('消息时间', self._format_time(create_time)),
                ]
                print_info(contents, '撤回消息')
            else:
                # 表情，图片, 链接或红包
                print(msg_type)
                print(msg)

    def web_wx_logout(self):
        url = self.base_uri + '/webwxlogout?redirect=1&type=0&skey=%s' % self.skey
        request_headers = self.headers

        data = {
            'sid': self.wxsid,
            'uin': self.wxuin,
        }

        res = self.s.post(url, data=data, headers=request_headers, timeout=REQUESTS_TIME_OUT)
        print(res)

    def show_login_user_info(self):
        """
        显示登录用户信息
        """
        nick_name = self.client_info['User']['NickName']
        sex = self.client_info['User']['Sex']
        contents = [
            format_info('昵称', nick_name),
            format_info('性别', ['-', '男', '女'][sex]),
        ]
        print_info(contents, '登录信息')

    def show_gh_info(self):
        """
        显示公众号、订阅号等信息
        """
        contents = []
        for member_item in self.client_contact['MemberList']:
            if member_item['ContactFlag'] * 8 == member_item['VerifyFlag']:
                nick_name = member_item['NickName']
                signature = member_item['Signature']
                address = ' - '.join([member_item['Province'], member_item['City']]) if member_item['City'] else \
                    member_item['Province']
                contents.append(output_line('>', '<'))
                contents.append(format_info('公众账号', nick_name))
                contents.append(format_info('个性签名', signature, False))
                contents.append(format_info('地址信息', address))
        print_info(contents, '公众账号')

    def get_group_member(self, group_code, member_code):
        """
        获取群组信息
        :param group_code:
        :param member_code:
        :return:
        """
        # 获取群组成员
        for group_item in self.client_group_contact['ContactList']:
            if group_code == group_item['UserName']:
                group_nick_name = group_item['NickName']
                group_display_name = group_item['DisplayName']
                group_info = group_nick_name
                if group_display_name:
                    group_info = '%s [%s]' % (group_nick_name, group_display_name)

                for member_item in group_item['MemberList']:
                    if member_code == member_item['UserName']:
                        member_nick_name = member_item['NickName']
                        member_display_name = member_item['DisplayName']
                        member_info = member_nick_name
                        if member_display_name:
                            member_info = '%s [%s]' % (member_nick_name, member_display_name)
                        return group_info, member_info
        # 获取群聊成员
        for group_item in self.client_info['ContactList']:
            if group_code == group_item['UserName']:
                group_nick_name = group_item['NickName']
                group_display_name = group_item['DisplayName']
                group_info = group_nick_name
                if group_display_name:
                    group_info = '%s [%s]' % (group_nick_name, group_display_name)

                for member_item in self.client_group_tmp_contact.get(group_code, {}).get('ContactList', []):
                    if member_code == member_item['UserName']:
                        member_nick_name = member_item['NickName']
                        member_info = member_nick_name
                        return group_info, member_info
        return '-', '-'

    def get_contact_member(self, member_code):
        """
        获取联系成员
        :param member_code:
        :return:
        """
        # for member_item in self.client_info['ContactList']:
        for member_item in self.client_contact['MemberList']:
            if member_code == member_item['UserName']:
                member_nick_name = member_item['NickName']
                member_remark_name = member_item['RemarkName']
                member_info = '%s [%s]' % (
                    member_nick_name, member_remark_name) if member_remark_name else member_nick_name
                return member_info
        user_info = self.client_info['User']
        return user_info['NickName'] if member_code == user_info['UserName'] else '-'

    @catch_keyboard_interrupt
    def run(self):
        self.get_uuid()
        self.get_qr_code()

        # 扫码登录
        while True:
            print('[微信扫码]')
            if not self.wait_for_login():
                continue
            print('[手机确认]')
            if not self.wait_for_login(0):
                continue
            break
        self.login()
        self.web_wx_init()
        self.web_wx_status_notify()

        self.web_wx_get_contact()               # 获取好友信息
        self.web_wx_get_group_contact()         # 获取群组成员
        self.web_wx_get_group_tmp_contact()     # 获取群聊成员

        self.show_login_user_info()
        self.show_gh_info()

        # 轮询消息
        while True:
            last_check_tc = time.time()
            retcode, selector = self.sync_check()
            if retcode == '1100':
                print('其他设备[手机]正在登录微信')
                # self.web_wx_logout()
                break
            if retcode == '1101':
                print('其他设备[电脑]正在登录微信')
                # self.web_wx_logout()
                break
            elif retcode == '0':
                if selector == '2':
                    # print('消息检查')
                    self.web_wx_sync()
                elif selector == '6':
                    print('红包来了, 还不去抢')
                    self.web_wx_sync()
                elif selector == '7':
                    print('手机操作')
                    self.web_wx_sync()
                elif selector == '0':
                    # print('没有消息')
                    time.sleep(1)
                else:
                    print('interesting selector: %s' % selector)
            # 消息间隔
            expend_tc = time.time() - last_check_tc
            if expend_tc <= 10:
                time.sleep(10 - expend_tc)


if __name__ == '__main__':
    wx_client = WXClient(debug=True)
    wx_client.run()
