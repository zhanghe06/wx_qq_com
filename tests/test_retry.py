#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: test_retry.py
@time: 2018-02-01 20:35
"""

import time
import unittest

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

RETRY_COUNT = 3     # 重试次数
RETRY_FACTOR = 1    # 补时系数

RETRY_TIME = RETRY_FACTOR * sum([2 * i for i in range(RETRY_COUNT)])

not_existed_url = 'http://www.notexisted.com'


class CommonTest(unittest.TestCase):
    """
    通用请求测试
    """

    def setUp(self):
        self.session_obj = requests.session()

    def test_request(self):
        """
        测试请求
        :return:
        """
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.session_obj.get(not_existed_url)

    def tearDown(self):
        self.session_obj.close()


class RetryTest(unittest.TestCase):
    """
    重试请求测试
    """

    def setUp(self):
        self.session_obj = requests.session()

        retries = Retry(total=RETRY_COUNT,      # 总共重试次数
                        connect=RETRY_COUNT,    # 连接超时重试次数
                        read=RETRY_COUNT,       # 读取超时重试次数
                        backoff_factor=RETRY_FACTOR,
                        status_forcelist=[500, 502, 503, 504])

        self.session_obj.mount('http://', HTTPAdapter(max_retries=retries))
        self.session_obj.mount('https://', HTTPAdapter(max_retries=retries))

    def test_request(self):
        """
        测试请求
        :return:
        """
        start_time = time.time()

        with self.assertRaises(requests.exceptions.ConnectionError):
            self.session_obj.get(not_existed_url)

        end_time = time.time()
        consumed_time = end_time - start_time

        self.assertGreater(consumed_time, RETRY_TIME)

    def tearDown(self):
        self.session_obj.close()


if __name__ == '__main__':
    unittest.main()
