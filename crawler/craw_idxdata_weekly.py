# -*- coding =utf-8 -*-
#encoding:utf-8
# coding = utf-8
#coding:utf-8
import sys 
reload(sys) 
sys.setdefaultencoding("utf-8")

import argparse
from selenium import webdriver
import  time  #调入time函数
import csv
import os
import re
from datetime import datetime
#from xvfbwrapper import Xvfb
import pandas as pd

from simple_io import IO
# 设置访问Hive用户名
client = IO.newHive('bjcaoxianteng')
database = 'ep_quant'

# 计算两个时间点的时间间隔，单位为分。
# time1和time2均为时间字符串，格式为:%Y年%m月%d日%H:%M
def delTime(time1, time2):
    
    time1 = datetime.strptime(time1, "%Y年%m月%d日%H:%M")
    time2 = datetime.strptime(time2, "%Y年%m月%d日%H:%M")
    deltime = (time1-time2).total_seconds()/60
    return int(deltime)

''' 获取数据源(存储在网页元素tr标价符left节点中)的时间串，
    网页格式为
    <tr id="historicEvent_353389" event_attr_id="135" event_timestamp="2017-09-07 06:00:00">
            <td class="left">2017年9月7日  (七月)</td>
            <td class="left">14:00</td>
            <td class="noWrap"><span class="redFont" title="弱于预期">0.0%</span></td>
            <td class="noWrap">0.6%</td>
            <td class="blackFont noWrap">-1.1%</td>
            <td class="icon center"><i class="diamondNewEmptyIcon"></i></td>
    </tr>
'''
def getTrTime(tr):
    timesp = tr.find_elements_by_class_name('left')
    timesp = timesp[0].text+timesp[1].text #获取年月和小时
    timesp = timesp.replace(' ','') # 去除空格
    start = timesp.find('(')
    end = timesp.find(')')
    if start!=-1 and end!=-1:
        timesp = timesp[0:start]+timesp[end+1:]# 去除括号间数据, 只留下 2017年9月7日14:00 作为输出
    return timesp

# 比较爬取的数据和最近爬取的时间点
def checkTimeRecord(new_trs, recent_record):
    if len(new_trs) ==0: # 未爬取新数据，返回all_old即全旧数据
        return 'all_old', -1
    start_time = getTrTime(new_trs[0]) # 数据越靠前，越新
    if delTime(recent_record, start_time)>=0:# 记录的时间比爬取的最新数据还要新，说明爬取的数据已爬过，舍弃，记为全旧
        return 'all_old',-1
    end_time = getTrTime(new_trs[-1]) # 如果记录的时间点比爬取数据的最旧数据还旧，说明爬取的数据全为新数据，记为全新
    if delTime(end_time, recent_record)>0: 
        return 'all_new',-1

    #不是全新或全旧，说明部分新，找出部分新的下标，使用二分查找
    start_index = 0
    end_index = len(new_trs)-1

    while start_index<=end_index:
        mid_index = (start_index+end_index)//2
        if delTime(getTrTime(new_trs[mid_index]), recent_record)>0:
            start_index = mid_index+1
        else:
            end_index = mid_index-1
    return 'part_new', start_index # 返回部分新标记和最新的临界下标，即[0:start_index]即为新数据

# 点击操作过程，爬取过程中需要模拟手工点击过程获取新数据
# driver: 获取网页信息驱动
# min_num: 数据量未发生改变次数，大于该次数说明无法获取更多数据，退出
# key: 网页id
# url: 网页url
# recent_record: 该网页(id标识)最近爬取的时间点,只爬取比该时间点新的数据
def click_unchanged(driver, min_num, key, url, recent_record):
    unchanged_num = 0
    old_num= 0
    while True:
        try:
            element = driver.find_element_by_id("showMoreHistory"+key) # 获取要点击的键
            style = element.get_attribute('style') # 标记符，点击完全部后该元素为 no display
            new_trs = driver.find_element_by_id("eventHistoryTable"+key).find_element_by_tag_name('tbody').find_elements_by_tag_name('tr') # 获取数据源
            result, index = checkTimeRecord(new_trs, recent_record) # 和历史记录时间点比较
            if result == 'all_old': #所有获取的数据均比历史记录旧，说明没有新数据更新，退出
                return []
            elif result == 'part_new': # 部分数据比历史记录新，返回最新数据
                return new_trs[0:index]

            # 所有数据均为新，继续获取
            if len(new_trs)==old_num: # 新获取的数据未变化，记录次数
                unchanged_num+=1
            else:
                old_num =len(new_trs)
                unchanged_num=0
            # min_num没发生改变，说明卡住,重启
            if unchanged_num>min_num:
                driver.get(url)
                time.sleep(1)
                unchanged_num=0
                old_num=0
                continue

            if style: # 已点击到底，返回
                return new_trs
        except Exception as err:
            print(err)
            break
                    
        # 每次刷新网页大小会变动，点击按钮会改变位置，需要实时追踪按钮位置点击
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(element).click().perform()
        time.sleep(0.5)

    return []
# 获取网页数据源，具体格式请看ppt
def get_allidxs(browseri, trs):
    idxs = []    
    for tr in trs:
        timesp = tr.find_elements_by_class_name('left')
        timesp = timesp[0].text+timesp[1].text
        idx = tr.find_elements_by_class_name('noWrap')
        real_idx = idx[0].find_element_by_tag_name('span').text
        pred_idx = idx[1].text
        idxs.append([timesp, real_idx, pred_idx])
    return idxs

# 把数据结果保存道文件内，idxs是一个sample_num * 3矩阵， 每一行一个记录，分别为: 时间、今值、预测值
def writelist2file(filepath, idxs):
    with open(filepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['时间', '今值', '预测值'])
        for idx in idxs:
            if len(idx)==3:
                writer.writerow(idx)

def write2hive(tablename, idxs):
    # 创建表格
    client.execute('CREATE TABLE IF NOT EXISTS '+database+'.'+tablename+'(time string, real string, predict string) STORED AS PARQUET')
    df = pd.DataFrame(idxs, columns=['time','real','predict'])
    client.insertAppend(database, tablename, df)

# 记录最新下载时间点，便于持续下载
def savecheckpoint(cpfile, checkpoint):
    # 保存记录点
    fopen = open(cpfile, 'w')
    for key in checkpoint.keys():
        fopen.write('%s %s\n'%(key, checkpoint[key]))
    fopen.close()

''' 爬取经济指标数据idx, 其中
# filename: 指标名
# url: 网页url
# browser: 浏览器驱动
# savedir: 保存位置
# checkpoint: 历史记录
# cpfile: 历史记录文件
'''
def craw_idxdata(filename, url, browser, savedir, checkpoint, cpfile):
    filepath = savedir+filename+'.csv'
    recent_record = '1900年01月01日00:00' # 最新记录时间点，默认值
    if filename in checkpoint.keys():
        recent_record = checkpoint[filename] # 存在最新记录点，更新

    m=re.search(r'[^-]+$', url) # 获取url最后'-'符后的数字，为该网页id
    if m:
        key = m.group(0)
    else:
        return
    browser.get(url) # 启动浏览器
    time.sleep(1)  #休眠0.3秒

    trs = click_unchanged(browser,5, key, url, recent_record) # 获取网页元素(存储数据源)
    idxs = get_allidxs(browser, trs) # 解析网页元素获取数据源
    #writelist2file(filepath, idxs) # 将数据源存储到文件
    if len(trs)==0:
        return
    write2hive(filename, idxs)
    checkpoint[filename] = getTrTime(trs[0]) # 存储点更新
    savecheckpoint(cpfile, checkpoint) # 存储点保存到文件

# 读取url配置文件，每行三个字段，用空格分开，分别为 idx英文名 idx中文名 idx的url
def read_rawdatas(filepath):
    fopen = open(filepath, 'r')
    if fopen is None:
        raise IOError('%s cannt open!'%filepath)

    names=[]
    urls=[]
    for line in fopen:
        line = line.replace('\n','') # 去除换行
        seg_list = line.split()
        if len(seg_list)==3: # 必须包含三个元素
            names.append(seg_list[0]) # 0位置英文名
            urls.append(seg_list[2]) # 2位置url
    fopen.close()
    return names, urls # 返回所有idx-name，idx-url对

# 读取记录文件，记录文件每行一条记录，两个字段用空格隔开，分别为idx-name和该idx最新爬取的数据时间点
def readcheckpoint(filepath):
    # 读取保存节点数据
    checkpoint ={}
    if not os.path.exists(filepath):
        return checkpoint
    fopen = open(filepath, 'r')
    if fopen is None:
        raise IOError('%s cannt open!'%(filepath))
    for line in fopen:
        line = line.replace('\n','')
        key, date = line.split() # 两个元素
        checkpoint[key]=date # 记录idx名和对应的日期
    fopen.close()
    return checkpoint

'''爬取所有的idx经济指标
# urlfile: 所有经济指标配置文件，每行为一种经济指标配置，三个字段，用空格隔开，分别为经济指标的:英文名,中文名，url
# savedir: 保存的文件目录
# cpfile: 保存的爬取最新记录时间文件
'''
def craw_allidx(urlfile, savedir, cpfile):
    #读取节点文件,filename, 最近读取日期
    filenames, urls = read_rawdatas(urlfile) # 读取配置文件
    checkpoint = readcheckpoint(cpfile) # 读取节点文件
    browser = webdriver.Chrome('/usr/local/bin/chromedriver') # 加载驱动
    name_urls = zip(filenames, urls) # 链接
    for name_url in name_urls:
        craw_idxdata(name_url[0], name_url[1], browser, savedir, checkpoint, cpfile) # 爬取每个经济指标
    print('craw over!')
    browser.quit()# 退出浏览器

def main(args):
    urlfile = args.urlfile # 配置参数
    savedir = args.savedir # 存储位置
    if not os.path.exists(savedir):
        os.makedirs(savedir) # 不存在就创建
    cpfile = savedir+args.cpfile # 节点文件

    #xvfb = Xvfb(width=1280, height=720)
    #xvfb.start()
    craw_allidx(urlfile, savedir, cpfile) # 爬取
    #xvfb.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="", description="help instruction") # 参数传递设置
    parser.add_argument("-urlfile", default="idx_urls.txt", help="the input data path.")#经济指标配置文件
    parser.add_argument("-savedir", default="../data/idxData/", help="the input data path.") #保存位置
    parser.add_argument("-cpfile", default="checkpoint.txt", help="the input data path.")#节点位置
    args = parser.parse_args()
    main(args)
