#!/usr/bin/env python
# -*- coding: utf8 -*-
import urllib.parse
import requests, re, gzip
from threading import Thread
import queue
import time
import json
from bs4 import BeautifulSoup
import os
import threading
import random

lock = threading.Lock()

timeStamp = time.time()
fileName = 'domain-{timeStamp}.txt'.format(timeStamp=timeStamp)
if not os.access(fileName, os.F_OK) or not os.access(fileName, os.F_OK):
    with open(fileName, 'w'):
        pass
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
}

session = requests.session()


# 保存到文件
def saveDomain(domain):
    lock.acquire()
    with open(fileName, 'r+') as fileHandler:
        fileData = fileHandler.read()
        if fileData.find(domain) == -1:
            fileHandler.write(domain + "\n")
    lock.release()


# 访问网页定义
def http_get(url):
    try:
        res = session.get(url, verify=True, headers=headers)
    except Exception as e:
        return False
    try:
        data = res.content.decode('utf-8')
    except:
        try:
            data = res.content.decode('gbk')
        except:
            try:
                data = gzip.decompress(res.content).decode()
            except:
                data = ''
    return data


# 获取域名
def getDomain(tmpStr):
    try:
        tmpStr = tmpStr.replace('<b>', '')
    except:
        tmpStr = ''
    try:
        domain = re.search(r'[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?', tmpStr).group()
    except:
        domain = False
    return domain


# 取出谷歌返回内容中的域名
def getDomains(data):
    try:
        soup = BeautifulSoup(data, 'html.parser')
    except:
        return []
    domainList = []
    for info in soup.find_all("h3", {'class': 'r'}):
        url = info.a['href']
        try:
            domain = re.search(r'[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?', url).group()
            domainList.append(domain)
        except:
            pass
    return domainList


# 返回谷歌一页的域名
def google(keyWord, pageNum):
    time.sleep(random.uniform(0, 3))
    url = 'https://www.google.com.hk/search?safe=strict&hl=zh-CN&site=webhp&source=hp&q=%s&start=%d' % (
        urllib.parse.quote(keyWord), pageNum * 10)
    data = http_get(url)
    domainList = getDomains(data)
    return domainList


def get_baidu_url(url):
    response = requests.get(url=url, verify=True, timeout=20, headers=headers)
    try:
        html = response.content
        decrypt_url = re.findall('<META http-equiv="refresh" content="0;URL=\'(.*?)\'"></noscript>', html)
    except TypeError:
        html = response.text
        decrypt_url = re.findall('<META http-equiv="refresh" content="0;URL=\'(.*?)\'"></noscript>', html)
    if decrypt_url:
        return decrypt_url
    else:
        return response.url


# 获取百度一页的域名
def baidu(keyWord, pageNum):
    time.sleep(0.5)
    url = "https://www.baidu.com/s?wd=%s&pn=%d" % (urllib.parse.quote(keyWord), pageNum * 10)
    data = http_get(url)
    reStr = 'href="(.*?)"\s+style="text-decoration:none;">'
    domainList = []
    for tmpStr in (re.findall(reStr, data)):
        try:
            tmpStr = tmpStr.split('"')[0]
            domain = get_baidu_url(tmpStr)
        except Exception:
            continue
        domain = getDomain(domain)
        if domain is not False:
            # print(domain)
            domainList.append(domain)
    # print(domainList)
    return domainList


# 获取360一页的域名
def so360(keyWord, pageNum):
    url = "http://www.so.com/s?q=%s&pn=%d" % (urllib.parse.quote(keyWord), pageNum)
    data = http_get(url)
    reStr = '<p class="res-linkinfo"><cite>(.*)</cite>'
    domainList = []
    for domainTmp in re.findall(reStr, data):
        domain = getDomain(domainTmp)
        if domain is not False:
            # print(domain)
            domainList.append(domain)
    # print(domainList)
    return domainList


# 获取手机360一页的域名
def mSo(keyWord, pageNum):
    url = "http://m.so.com/nextpage?q=%s&pn=%d" % (urllib.parse.quote(keyWord), pageNum)
    data = http_get(url)
    reStr = 'data-pcurl="(.*?)" data-jss='
    domainList = []
    for domainTmp in re.findall(reStr, data):
        domain = getDomain(domainTmp)
        if domain is not False:
            domainList.append(domain)
    return domainList


# 获取手机百度一页的域名
def mBaidu(keyWord, pageNum):
    url = "http://m.baidu.com/s?word=%s&pn=%d" % (urllib.parse.quote(keyWord), pageNum * 10)
    data = http_get(url)
    reStr = '<div class="c-showurl c-line-clamp1"><span class="c-showurl">(.*?)</span>'
    domainList = []
    for domainTmp in re.findall(reStr, data):
        domain = getDomains(domainTmp)
        if domain is not False:
            # print(domain)
            domainList.append(domain)
    # print(domainList)
    return domainList


class Scrapy(Thread):
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.start()

    def run(self):
        time.sleep(0.3)
        i = 0
        domainListTmp = []
        while True:
            try:
                task_str = self.tasks.get(timeout=3)
            except queue.Empty as empyt:
                break
            finally:
                try:
                    self.tasks.task_done()
                except ValueError as taskError:
                    pass

            task = json.loads(task_str)
            key = task.get('key')
            i = task.get('page')
            try:
                start = time.time()
                domainListTmp.extend(google(key, i))
                domainListTmp.extend(baidu(key, i))
                domainListTmp.extend(so360(key, i))
                domainListTmp.extend(mBaidu(key, i))
                print('[INFO]: 关键词:%s,页数:%d,Domain:%s,耗时:%ss' % (key, i, len(domainListTmp), int( time.time() - start)))
                # 开始验证域名
                for domainTmp in domainListTmp:
                    domain = getDomain(domainTmp)
                    if domain is not False:
                        saveDomain(domain)
            except:
                pass


class Task_Manager(Thread):
    """任务管理"""

    def __init__(self, tasks, keyList, page):
        Thread.__init__(self)
        self.__tasks = tasks
        self.keyList = keyList
        self.page = page
        print('[{}] INFO: 线程启动'.format(
            self.__class__.__name__))
        self.start()

    def run(self):
        keyList = self.keyList.split("\n")
        for key in keyList:
            for i in range(0, self.page + 1):
                self.loop_task(json.dumps(dict(page=i, key=key)))

    def loop_task(self, key):
        # 将任务放入 队列中
        self.__tasks.put(key)


class Start_Task:
    """启动所有任务线程"""

    def __init__(self, num_threads, key, page):
        self.tasks = queue.Queue()  # 队列任务最多存放10条
        # self.tasks.put(key)
        for _ in range(num_threads):
            print('[{}] INFO: 线程启动'.format(self.__class__.__name__))
            Scrapy(self.tasks)
        Task_Manager(self.tasks, key, page)

    def wait_completion(self):
        self.tasks.join()


if __name__ == '__main__':
    start = time.time()
    # 第一个是线程数 第二个是关键词 第三个页数
    line = None
    with open('keyword.txt') as file_handle:
        line = file_handle.read()

    if line is not None:
        start_task = Start_Task (10, line, 75)
        start_task.wait_completion()
    print('本次查询耗时:%ss' % (int(time.time() - start),))
