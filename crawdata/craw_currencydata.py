# -*- coding =utf-8 -*-


# coding = utf-8
import argparse
from selenium import webdriver
import  time  #调入time函数
import csv
import os
import re
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys

def getCurrencyData(driver):
    currencies = []
    
    try:
        start = time.time()
        table = driver.find_element_by_xpath("//table[@id='curr_table']")
        end = time.time()
        print('table find time:%f'%(end-start))
        #table = driver.find_element_by_id('curr_table')
        trs = table.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
        start = time.time()
        print('trs time:%lf'%(start-end))
    except Exception as err:
        print(err)
        time.sleep(1000)

    for tr in trs:
        start = time.time()
        tds = tr.find_elements_by_tag_name('td')
        end = time.time()
        print('tr find tds time:%lf,tds len:%d'%(end-start, len(tds)))
        currencies.append([tds[0].text, tds[1].text, tds[2].text, tds[3].text, tds[4].text, tds[5].text])
    return currencies

def writelist2file(filepath, currencies):
    num = len(currencies)
    with open('%s'%filepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['日期', '最新股价', '开盘', '高', '低', '百分比变化'])
        for i in range(num):
            if len(currencies[i])==6:
                writer.writerow(currencies[i])

def selectTime(driver, startTime, endTime):
    # 点击日期选择
    element = driver.find_element_by_id('widgetFieldDateRange')
    actions = webdriver.ActionChains(driver)
    actions.move_to_element(element).click().perform()
    
    time.sleep(0.5)
    print(startTime)
    

    startDateElement = driver.find_element_by_id('startDate')
    startDateElement.clear();
    startDateElement.send_keys(startTime)
    
    endDateElement = driver.find_element_by_id('endDate')
    endDateElement.clear();
    endDateElement.send_keys(endTime)
    
    #endDateElement.send_keys(Keys.ENTER)
    
    applyBtn = driver.find_element_by_id('applyBtn')
    actions = webdriver.ActionChains(driver)
    actions.move_to_element(applyBtn).click().perform()
    time.sleep(0.5)

def getDuringTime(year):
    # 获取某一年的起止时间
    year = str(year)
    start = year+'/01/01'
    end = year+'/12/31'
    return start, end

def craw_currencydata(savedir, filename, url, driver):
    if not os.path.exists(savedir):
        os.makedirs(savedir)

    driver.get(url)
    time.sleep(2)  #休眠0.3秒
    
    sel = Select(driver.find_element_by_xpath("//select[@id='data_interval']"))
    
    for option in sel.options:
        
        filepath = os.path.join(savedir, filename+'_'+option.text+'.csv')
        if os.path.exists(filepath):
            print('%s has exist!'%filepath)
            continue
        sel.select_by_visible_text(option.text) # 选择粒度，每日、周、月
        all_currencies=[]
        for year in range(2017, 1990,-1):
            start,end = getDuringTime(year)
            selectTime(driver, start, end)
            year_currencies = getCurrencyData(driver)
            all_currencies.extend(year_currencies)
        writelist2file(filepath, all_currencies)

def read_rawdatas(filepath):
    fopen = open(filepath, 'r')
    if fopen is None:
        raise IOError('%s cannt open!'%filepath)

    names=[]
    urls=[]
    for line in fopen:
        line = line.replace('\n','')
        seg_list = line.split()
        if len(seg_list)==2:
            names.append(seg_list[0])
            urls.append(seg_list[1])
    fopen.close()
    return names, urls
    
def craw_allcurrency(urlfile, savedir):
    filenames, urls = read_rawdatas(urlfile)
    browser = webdriver.Chrome('./chromedriver')
    name_urls = zip(filenames, urls)
    for name_url in name_urls:
        craw_currencydata(savedir, name_url[0], name_url[1], browser)
    print('craw over!')
    browser.quit()

def main(args):
    urlfile = args.urlfile
    savedir = args.savedir
    craw_allcurrency(urlfile, savedir)

if __name__ == '__main__':
    parser = argparse.argumentparser(usage="", description="help instruction")
    parser.add_argument("-urlfile", default="currency_urls.txt", help="the input data path.")
    parser.add_argument("-savedir", default="./currencydata/", help="the input data path.")
    args = parser.parse_args()
    
    main(args)
