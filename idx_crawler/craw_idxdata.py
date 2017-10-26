# -*- coding =utf-8 -*-


# coding = utf-8
import argparse
from selenium import webdriver
import  time  #调入time函数
import csv
import os
import re
import time

def click_unchanged(driver, min_num, key, url):
    unchanged_num = 0
    old_num= 0
    while True:
        try:
            element = driver.find_element_by_id("showMoreHistory"+key)
            style = element.get_attribute('style')
            new_trs = driver.find_element_by_id("eventHistoryTable"+key).find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
            # 判断获取的idx条目是否发生改变
            if len(new_trs)==old_num:
                unchanged_num+=1
            else:
                old_num =len(new_trs)
                unchanged_num=0
            # min_num没法生改变，说明卡住,重启
            if unchanged_num>min_num:
                driver.get(url)
                time.sleep(1)
                unchanged_num=0
                old_num=0
                continue

            if style:
                return new_trs
        except Exception as err:
            print(err)
            break
                    
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(element).click().perform()
        time.sleep(0.5)

    return []
def get_allidxs(driver, trs):
    idxs = []
    js = """
    var parent = arguments[0];
    var timesp = parent.getElementsByClassName('left');
    var date = timesp[0].innerText + timesp[1].innerText;
    var idx = parent.getElementsByClassName('noWrap');
    var real_idx = idx[0].innerText;
    var pred_idx = idx[1].innerText;
    return date+','+real_idx+','+pred_idx;
    """
    for tr in trs: 
        result = driver.execute_script(js, tr)
        idxs.append(result.split(','))
    return idxs

def writelist2file(filepath, idxs):
    with open(filepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['时间', '今值', '预测值'])
        for idx in idxs:
            if len(idx)==3:
                writer.writerow(idx)

def craw_idxdata(filename, url, browser, savedir):
    filepath = savedir+filename+'.csv'
    if os.path.exists('%s'%(filepath)):
        print('%s has exist! skip'%filepath)
        return

    m=re.search(r'[^-]+$', url)
    if m:
        key = m.group(0)
    else:
        return
    browser.get(url)
    time.sleep(1)  #休眠0.3秒

    trs = click_unchanged(browser,5, key, url)
    idxs = get_allidxs(browser, trs)
    writelist2file(filepath, idxs)

def read_rawdatas(filepath):
    fopen = open(filepath, 'r')
    if fopen is None:
        raise IOError('%s cannt open!'%filepath)

    names=[]
    urls=[]
    for line in fopen:
        line = line.replace('\n','')
        seg_list = line.split()
        if len(seg_list)==3:
            names.append(seg_list[1])
            urls.append(seg_list[2])
    fopen.close()
    return names, urls


def craw_allidx(urlfile, savedir):
    #读取节点文件,filename, 最近读取日期
    filenames, urls = read_rawdatas(urlfile)
    browser = webdriver.Chrome()
    name_urls = zip(filenames, urls)
    for name_url in name_urls:
        print('crawler')
        craw_idxdata(name_url[0], name_url[1], browser, savedir)
    print('craw over!')
    browser.quit()

def main(args):
    urlfile = args.urlfile
    savedir = args.savedir
    craw_allidx(urlfile, savedir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="", description="help instruction")
    parser.add_argument("-urlfile", default="idx_urls.txt", help="the input data path.")
    parser.add_argument("-savedir", default="../datas/idxData/", help="the input data path.")
    
    args = parser.parse_args()
    main(args)
