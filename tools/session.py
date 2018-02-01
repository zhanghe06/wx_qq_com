#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: session.py
@time: 2017-12-30 12:04
"""


import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter


RETRY_COUNT = 3  # 重试次数
session_obj = requests.session()

retries = Retry(total=RETRY_COUNT,      # 总共重试次数
                connect=RETRY_COUNT,    # 连接超时重试次数
                read=RETRY_COUNT,       # 读取超时重试次数
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504])

session_obj.mount('http://', HTTPAdapter(max_retries=retries))
session_obj.mount('https://', HTTPAdapter(max_retries=retries))
