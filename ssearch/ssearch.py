#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on 2018/9/28
import sys
from hashlib import md5
import requests
import uuid
import argparse
import re
import time
import hashlib
import random

def TTK(a, b):
    for d in range(0, len(b) - 2, 3):
        c = b[d + 2]
        c = ord(c[0]) - 87 if 'a' <= c else int(c)
        c = a >> c if '+' == b[d + 1] else a << c
        a = a + c & 4294967295 if '+' == b[d] else a ^ c
    return a

def getTk(text):
    '''
    获取tk 值
    :param text:
    :return:
    '''
    b = 406644
    e = list()
    for x in range(len(text)):
        m=ord(text[x])
        if 128 > m:
            e.insert(x,m)
        elif 2048 > m:
            e.append(m >> 6 | 192)
        elif (55296 == (m & 64512)) and (x + 1 < len(text)) and (56320 == (ord(text[x + 1]) & 64512)):
            x+=1
            m = 65536 + ((m & 1023) << 10) + (ord(text[x]) & 1023)
            e.append(m >> 18 | 240)
            e.append(m >> 12 & 63 | 128)
        else:
            e.append(m >> 12 | 224)
            e.append(m >> 6 & 63 | 128)
            e.append(m & 63 | 128)
    a=b
    for d in range(len(e)):
        a += e[d]
        a = TTK(a, '+-a^+6')
    a = TTK(a, "+-3^+b+-f")
    a ^= 3293161072 or 0
    if 0 > a: a = (a & 2147483647) + 2147483648
    a %= 1E6
    return str(int(a)) + "." + str(int(a)^b)

def signlib(text):
    '''
    md5加密
    :return:
    '''
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()


class Language:
    ch = u'中文'


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def fm(s):
    """
    clear rich text
    :param s:
    :return:
    """
    return re.sub(r'<.*?>', '', s)


def search(text):
    print(u'{}using sougou translate search [{}] ...{}'.format(Bcolors.HEADER, text, Bcolors.ENDC))

    url = 'https://fanyi.sogou.com/reventondc/translate'
    _from = 'auto'
    to = 'zh-CHS'
    s = md5('{}{}{}{}'.format(_from, to, text, 'front_9ee4f0a1102eee31d09b55e4d66931fd').encode()).hexdigest()
    param = {'from'           : _from,
             'to'             : to,
             'client'         : 'pc',
             'fr'             : 'browser_pc',
             'text'           : text,
             'pid'            : 'sogou-dict-vr',
             'useDetect'      : 'on',
             'useDetectResult': 'on',
             'needQc'         : 1,
             'uuid'           : uuid.uuid4(),
             'oxford'         : 'on',
             'isReturnSugg'   : 'off',
             's'              : s}

    resp = requests.post(url=url, data=param).json()
    detect = resp.get('detect', {}).get('language')

    sys.stdout.write("\033[F")  # back to previous line
    sys.stdout.write("\033[K")  # clear line

    print(Bcolors.OKGREEN)
    print(u'{0: >10} : {1}'.format('text', resp.get('translate', {}).get('text')))
    print(u'{0: >10} : {1}'.format('dit', resp.get('translate', {}).get('dit')))

    # print(json.dumps(resp))
    d = resp.get('dictionary')
    if d:
        for item in d['content']:
            phonetic = item.get('phonetic', [])
            if isinstance(phonetic, list):
                for p in phonetic:
                    print(u'{0: >10} : {1}'.format(p['type'], p['text']))

            for u in item.get('usual', []):
                print(u'{0: >10} : {1}'.format(u['pos'], fm(' '.join(u['values']))))
    if detect == Language.ch and d:
        for item in d['content']:
            cat = item.get('category', [])
            for c in cat:
                for sense in c['sense']:
                    print('{:>10} : {}'.format('sense', sense['description']))

    print('')

def google(text):
    '''
    谷歌翻译
    :param text:
    :return:
    '''
    print(u'{}using google translate search [{}] ...{}'.format(Bcolors.HEADER, text, Bcolors.ENDC))
    tk = getTk(text)
    zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
    match = zh_pattern.search(text)
    url = "https://translate.google.cn/translate_a/" \
                   "single?client=t&sl={sl}&tl={tl}&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie" \
                   "=UTF-8&oe=UTF-8&otf=1&ssel=0&tsel=0&kc=1&" \
                   "tk={tk}&q={text}"
    if match:
        result = requests.get(url.format(sl="zh-CN",tl="en",tk=tk,text=text)).content.decode('utf-8')
    else:
        result = requests.get(url.format(sl="en",tl="zh-CN",tk=tk,text=text)).content.decode('utf-8')
    end = result.find("\",")
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")
    if end > 4:
        print(Bcolors.OKGREEN)
        print('{0: >10} : {1}'.format('text', text))
        print('{0: >10} : {1}'.format('dit', result[4:end]))



def youdao(text):
    '''
    有道翻译
    :param text:
    :return:
    '''
    print(u'{}using youdao translate search [{}] ...{}'.format(Bcolors.HEADER, text, Bcolors.ENDC))
    url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
    headers = {
        'Cookie': 'OUTFOX_SEARCH_USER_ID=-2022895048@10.168.8.76;',
        'Referer': 'http://fanyi.youdao.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; rv:51.0) Gecko/20100101 Firefox/51.0',
    }
    salt=str(int(time.time() * 1000) + random.randint(0, 10))
    data = {
        'i': text,
        'from': 'AUTO',
        'to': 'AUTO',
        'smartresult': 'dict',
        'client': 'fanyideskweb',
        'salt': salt,
        'sign': signlib("fanyideskweb" + text +salt + "ebSeFb%=XZ%T[KZ)c(sy!"),
        'doctype': 'json',
        'version': '2.1',
        'keyfrom': 'fanyi.web',
        'action': 'FY_BY_CL1CKBUTTON',
        'typoResult': 'true'
    }
    result = requests.post(url, data=data, headers=headers).json()
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")
    print('{0: >10} : {1}'.format('text', text))
    print('{0: >10} : {1}'.format('dit', result.get("translateResult",{})[0][0].get("tgt")))

def main():
    parser = argparse.ArgumentParser(description='search tool')

    parser.add_argument('text', nargs='?', help='search content')
    parser.add_argument('-e', nargs='+', help='search engineer')
    parser.add_argument("-g", nargs='+',help="google translate")
    parser.add_argument("-y", nargs='+', help="youdao translate")
    args = parser.parse_args()
    if args.text:
        search(args.text)
    elif args.g:
        google(args.g[0])
    elif args.y:
        youdao(args.y[0])
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
