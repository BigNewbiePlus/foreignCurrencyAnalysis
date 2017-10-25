# -*- coding=utf-8 -*-
import argparse
import os
import pandas as pd
import time
import numpy as np
import sys

from datetime import datetime

timeinterval=[5, 10, 15, 20, 25, 30]
threshold = [0.002, 0.003, 0.004]

def showbar(info):
    info = '\r'+info
    sys.stdout.write(info)
    sys.stdout.flush()
def extractsingconfg(segs):
    # 提取单条配置信息
    idxs = segs[0].split('-')
    cur = segs[1].split('-')[1].upper()+'5'
    pairs = [[idx,cur] for idx in idxs]
    return pairs, idxs, cur


def getchildfiles(path):
    children = []
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        children.append(child)
    return children
    
def getfilemap(paths,keys):
    paths_map={}
    for path in paths:
        for key in keys:
            if key in path:
                if key not in paths_map.keys():
                    paths_map[key]=[]
                paths_map[key].append(path)
                break
    return paths_map
def getallfilepath(allidxs, allcurs, idxdir, curdir):
    filepaths = {}
    idxfilepaths = getchildfiles(idxdir)
    curfilepaths = getchildfiles(curdir)
    dict1 = getfilemap(idxfilepaths, allidxs)
    dict2 = getfilemap(curfilepaths, allcurs)
    dictMerged2=dict(dict1, **dict2)
    return dictMerged2

def readconfg(confgfile, idxdir, curdir):
    fopen = open(confgfile)
    if fopen is None:
        raise IOError('%s cannt open!'%(confgfile))
    allpairs=[]
    allidxs=[]
    allcurs=[]
    for line in fopen:
        line = line.replace('\n', '')
        seg = line.split()
        if len(seg)!=2:
            continue
        pairs, idxs, cur = extractsingconfg(seg)
        allpairs.extend(pairs)
        allidxs.extend(idxs)
        allcurs.append(cur)
    allidxs = list(set(allidxs))
    allcurs = list(set(allcurs))
    filepaths = getallfilepath(allidxs, allcurs, idxdir, curdir)
    fopen.close()
    return allpairs, filepaths
def writeStaticResult(fwrite, title, freq):

    fwrite.write(title+'\n')
    fwrite.write('时间\t')
    for eachtime in timeinterval:
        fwrite.write('%d分\t'%eachtime)
    fwrite.write('\n')

    cnt=0
    for i in range(len(threshold)):
        fwrite.write('%%%.3f\t'%(threshold[i]*100))

        for j in range(len(timeinterval)):
            fwrite.write('%%%.3f\t'%(freq[cnt]*100))
            cnt+=1
        fwrite.write('\n')

def writeAveResult(fwrite, title, thre):
    fwrite.write(title+'\n')
    fwrite.write('时间\t')
    for eachtime in timeinterval:
        fwrite.write('%d分\t'%eachtime)
    fwrite.write('\n')

    fwrite.write('均值\t')
    for i in range(len(timeinterval)):
        fwrite.write('%%%.3f\t'%(thre[i]*100))
    fwrite.write('\n')
def writeTotalResult(fwrite, title, total_num):
    fwrite.write(title+'\t:')
    for num in total_num:
        fwrite.write('%d\t'%num)
    fwrite.write('\n\n')

def checkpoint(cppath, key, result,filt):
    fopen = open(cppath, 'a')
    if fopen is None:
        raise IOError('%s cannt open!'%(cppath))
    fopen.write(key+'\n\n')
    # 标记该数据是否记录，True为记录
    flag=False
    for i in range(len(result[2])):
        if result[2][i]>result[3][i]:
            flag=True
            break
    # 如果不允许过滤，记录数据
    if filt == False:
        flag=True
    if flag is False:
        fopen.close()
        return
    writeTotalResult(fopen, '经济指标各分钟出现总个数', result[0])
    writeTotalResult(fopen, '正常情况各分钟出现总个数', result[1])
    writeStaticResult(fopen, '经济指标公布后外汇波动', result[2])
    writeStaticResult(fopen, '正常情况下波动', result[3])
    writeAveResult(fopen, '平均波动幅度', result[4])
    fopen.write('\n\n')
    
    fopen.close()

def preprocess_idxtime(idxnp):
    # 预处理idx数据，处理时间
    #获取第一列时间，处理
    for i in range(len(idxnp)):
        date = idxnp[i][0]
        date = date.replace(' ','')
        
        start = date.find('(')
        end = date.find(')')
        if start!=-1 and end!=-1:
            date=date[0:start]+date[end+1:]
        #如a = "2013-10-10 23:40:00",想改为 a = "2013/10/10 23:40:00"
        #方法:先转换为时间数组,然后转换为其他格式
        timeArray = time.strptime(date, "%Y年%m月%d日%H:%M")
        otherStyleTime = time.strftime("%Y.%m.%d %H:%M", timeArray)
        idxnp[i][0]=otherStyleTime

def getfilename(filepath):
    start = filepath.rfind('/')
    end = filepath.rfind('.')
    filename = filepath[start+1:end]
    return filename

# 比较两者时间间隔，输出为<<,<,>,==
def delTime(time1, time2):
    
    time1 = datetime.strptime(time1, "%Y.%m.%d %H:%M")
    time2 = datetime.strptime(time2, "%Y.%m.%d %H:%M")
    deltime = (time1-time2).total_seconds()/60
    return int(deltime)

def calcur(curnp, cur_index, cur_freq, cur_threshold, cur_total):
    next_index = cur_index+1
    start_val = float(curnp[cur_index][5])
    max_highval = -1
    min_lowval = 12343847837
    while next_index<len(curnp):
        deltime = delTime(curnp[next_index][0]+' '+curnp[next_index][1], curnp[cur_index][0]+' '+curnp[cur_index][1])
        if deltime>timeinterval[-1]:
            break
        max_highval = max(max_highval, float(curnp[next_index][3]))
        min_lowval = min(min_lowval, float(curnp[next_index][4]))
        index = deltime//5-1
        ave = (max_highval-min_lowval)/start_val
        cur_threshold[index]+=ave
        cur_total[index]+=1
        for i in range(len(threshold)):
            if ave>= threshold[i]:
                cur_freq[i*len(timeinterval)+index]+=1
        next_index+=1


def calidx2cur(idxtime, curnp, cur_index, idx2cur_freq, idx2cur_total):
    next_index = cur_index+1
    start_val = float(curnp[cur_index][5])
    max_highval=-1
    min_lowval = 12237848

    while next_index<len(curnp):
        deltime = delTime(curnp[next_index][0]+' '+curnp[next_index][1], idxtime)
        if deltime>timeinterval[-1]:
            break
        max_highval = max(max_highval, float(curnp[next_index][3]))
        min_lowval = min(min_lowval, float(curnp[next_index][4]))
        index = deltime//5-1
        idx2cur_total[index]+=1
        ave = (max_highval-min_lowval)/start_val
        for i in range(len(threshold)):
            if ave>= threshold[i]:
                idx2cur_freq[i*len(timeinterval)+index]+=1
        next_index+=1

# 计算外汇本身波动
def curanalysis(curfilepath):
    curfilename = getfilename(curfilepath)
    curnp = pd.read_csv(curfilepath).values
    cur_len = len(curnp)
    #外汇在不同时间和阈值下频率
    cur_freq = np.zeros(len(timeinterval)*len(threshold))
    #外汇整体阈值平均值
    cur_threshold = np.zeros(len(timeinterval))
    cur_total = np.zeros(len(timeinterval))
    cur_index=0
    while cur_index<cur_len:
        # 计算外汇本身数据波动状况
        calcur(curnp, cur_index, cur_freq, cur_threshold, cur_total)
        cur_index+=1
        if cur_index%1000==0:
            showbar('%s:%d'%(curfilename, cur_index))

    for i in range(len(cur_total)):
        cur_threshold[i] = cur_threshold[i]/cur_total[i]
        for j in range(len(threshold)):
            index = j*len(timeinterval)+i
            cur_freq[index] = cur_freq[index]/cur_total[i] 
    return cur_total, cur_freq, cur_threshold

def idxanalysis(idxfilepath, curfilepath):
    idxfilename = getfilename(idxfilepath)
    curfilename = getfilename(curfilepath)
    
    # 读取数据
    idxnp = pd.read_csv(idxfilepath).values
    curnp = pd.read_csv(curfilepath).values


    #预处理idx文件
    preprocess_idxtime(idxnp)

    #比较时间
    idx_len = len(idxnp)
    cur_len = len(curnp)

    idx_index=idx_len-1
    cur_index=0;
    
    #经济指标公布对外汇影响个数
    idx2cur_total = np.zeros(len(timeinterval))
    #公布后各分钟内在不同阈值下的波动频率
    idx2cur_freq = np.zeros(len(timeinterval)*len(threshold))
    cnt=0
    while idx_index>=0 and cur_index<cur_len:
        cnt+=1
        if cnt%1000==0:
            showbar('%s___%s:%d'%(idxfilename, curfilename, cnt))

        deltime = delTime(idxnp[idx_index][0], curnp[cur_index][0]+' '+curnp[cur_index][1])

        if deltime<0 and -deltime>timeinterval[-1]:
            # 经济指标太旧，下一个
            idx_index-=1
        elif deltime>0: 
             # 经济指标时间较新，后移
            cur_index+=1
        else:
            calidx2cur(idxnp[idx_index][0], curnp, cur_index, idx2cur_freq, idx2cur_total)
            # 计算经济指标发布后波动
            idx_index-=1
            cur_index+=1
    

    for i in range(len(idx2cur_total)):
        for j in range(len(threshold)):
            index = j*len(timeinterval)+i
            idx2cur_freq[index] = idx2cur_freq[index]/idx2cur_total[i]
    return idx2cur_total, idx2cur_freq

def readcheckpoint(filepath):
    history_keys=[]
    if not os.path.exists(filepath):
        return history_keys

    fopen = open(filepath, 'r')
    if fopen is None:
        raise IOError('%s cannt open'%filepath)

    for line in fopen:
        if line.find('___')!=-1:
            key = line.replace('\n', '')
            history_keys.append(key)
    return history_keys


def idx2curanalysis(confgfile, idxdir, curdir, savedir, cpfile, filt):
    # 经济指标对外汇波动影响分析
    pairs, filepaths = readconfg(confgfile, idxdir, curdir)
    #研究每一个指标对外汇影响程度
    cppath = os.path.join(savedir,cpfile) 
    history_keys = readcheckpoint(cppath)
    num=1
    for pair in pairs:
        idxsfilepath = filepaths[pair[0]]
        curfilepath = filepaths[pair[1]][0]# 只有一个
        cur_total=None
        cur=None
        cur_thre=None
        for idxfilepath in idxsfilepath:
            idxfilename = getfilename(idxfilepath)
            curfilename = getfilename(curfilepath)
            key = idxfilename+'___'+curfilename
            if key in history_keys:
                print('%s has processed!skip'%key)
                continue
            if cur_total is None and cur is None and cur_thre is None:
                cur_total, cur, cur_thre = curanalysis(curfilepath)
            print('\nprocess seq:%d, %s'%(num, key))
            idx2cur_total, cur2idx = idxanalysis(idxfilepath, curfilepath)
            result=[idx2cur_total, cur_total, cur2idx, cur, cur_thre]
            history_keys.append(key)
            checkpoint(cppath, key, result,filt)
            num+=1

def main(args):
    confgfile = args.confgfile
    idxdir = args.idxdir
    curdir = args.curdir
    savedir = args.savedir
    cpfile = args.cpfile
    filt = args.filt

    idx2curanalysis(confgfile, idxdir, curdir, savedir, cpfile, filt)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="", description="help instruction")
    parser.add_argument("-confgfile", action='store', default="test.conf", help="the input data path.")
    parser.add_argument("-idxdir", action='store', default="../datas/idxData/", help="the input data path.")
    parser.add_argument("-curdir", action='store', default="../datas/curData5/", help="the input data path.")
    parser.add_argument("-savedir", action='store', default="./result/", help="the input data path.")
    parser.add_argument("-cpfile", action='store', default="./checkpoint.txt", help="the input data path.")
    parser.add_argument("-filt", action='store_true', default=False, help="the input data path.")
    args = parser.parse_args()
    
    main(args)
