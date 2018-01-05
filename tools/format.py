#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: format.py
@time: 2017-12-30 12:03
"""


from config import current_config

LINE_LENGTH = current_config.LINE_LENGTH


def _len(s):
    """
    占位长度（中文占用2个）
    :param s:
    :return:
    """
    s = str(s) if isinstance(s, int) else s
    length = len(s)
    utf8_length = len(s.encode('utf-8'))
    length = (utf8_length - length) / 2 + length
    return length


def _truncate(s, length=26):
    """
    字符串截断
    :param s:
    :param length:
    :return:
    """
    t_a = []
    t_t = []
    t_l = 0
    for i in s:
        t_l += _len(i)
        if t_l > length:
            t_a.append(u''.join(t_t))
            t_l = _len(i)
            t_t = []
        t_t.append(i)
    if t_t:
        t_a.append(u''.join(t_t))
    return t_a


def format_info(k, v, truncate=True):
    """
    格式化输出单行信息
    :param k:
    :param v:
    :param truncate:
    :return:
    """
    v = str(v) if isinstance(v, int) else v
    # 如果长度不够，忽略截取
    if _len(v) <= LINE_LENGTH - 1 - _len(k):
        return u' '.join([k, v.rjust(LINE_LENGTH - _len(k) - 1 - (_len(v) - len(v)))])
    s = []
    first = True
    for i in _truncate(v, LINE_LENGTH - 1 - _len(k)):
        if first:
            # s.append(u' '.join([k, i.rjust(LINE_LENGTH - _len(k) - 1 - (_len(i) - len(i)))]))
            s.append(u' '.join([k, i]))
            first = False
        else:
            # s.append(u' '.join([u' '*_len(k), i.rjust(LINE_LENGTH - _len(k) - 1 - (_len(i) - len(i)))]))
            s.append(u' '.join([u' '*_len(k), i]))
    if not s:
        return k
    if truncate:
        t = s[0]
        # 单条信息，靠右对齐
        if len(s) == 1:
            return u' '.join([k, v.rjust(LINE_LENGTH - _len(k) - 1 - (_len(v) - len(v)))])
        if _len(t) % 2 == 0:
            return '%s.' % t
        else:
            return '%s..' % t[:-1] if _len(t[-1]) == 2 else '%s.' % t[:-1]
    return u'\n'.join(s)


def print_info(contents, topic=None):
    """
    输出信息
    :param contents:
    :param topic:
    :return:
    """
    if topic:
        print('\n[%s]' % topic)
    contents.insert(0, '-' * LINE_LENGTH)
    contents.append('-' * LINE_LENGTH)
    print('\n'.join(contents))


def output_line(start='-', end='-'):
    return '%s%s%s' % (start, '-' * (LINE_LENGTH - len(start) - len(end)), end)


def test():
    """
    等宽字体输出信息对称
    [微信名片]
    -----------------------------------
    消息来源 1科学上网科学上网科学上网
             科学上网科学上网科学上网12
             34567890123456789012345678
             科学上网科学上网科学上网
    消息来源 123科学上网科学上网科学上.
    消息来源 1234科学上网科学上网科学..
    消息来源 科学上网科学上网科学上网1.
    消息内容                       [强]
    消息时间        2017-12-29 17:01:05
    -----------------------------------
    :return:
    """
    contents = [
        format_info(u'消息来源', u'1科学上网科学上网科学上网科学上网科学上网科学上网1234567890123456789012345678科学上网科学上网科学上网', False),

        format_info(u'消息来源', u'123科学上网科学上网科学上网科'),
        format_info(u'消息来源', u'1234科学上网科学上网科学上网科'),
        format_info(u'消息来源', u'科学上网科学上网科学上网1234科'),

        format_info(u'消息内容', u'[强]'),
        format_info(u'消息时间', u'2017-12-29 17:01:05'),
    ]
    print_info(contents, u'微信名片')


if __name__ == '__main__':
    test()
