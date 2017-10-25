#!/bin/sh

cd /usr/src/app/crawler

/usr/src/app/crawler/anaconda/bin/python ./craw_idxdata_weekly.py -urlfile ./idx_urls.txt -savedir ./
echo 'one time'

