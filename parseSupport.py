__author__ = 'isabella'

import os
import csv
import os.path
import datetime
import sys


code1 = "True if '<event1>' in dict else False"
# code2 = "for idx in range(0,len(list1),2):\n" \
#         "   print ('hi')"

def avgShopTime(timeList):
    shopTime = 0
    try:
        #global code2
        #list1 = timeList
        #result = eval(code2)
        for idx in range(0,len(timeList),2):
            shopTime += timeList[idx+1]-timeList[idx]
    except Exception,ex:
        print ex
        raise Exception
        return 0
    return shopTime

def getBuyerShopTime(valDict,evt,timeEvt):

    shopTime = 0
    try:
        dict = valDict
        global code1
        code1 = code1.replace("<event1>",evt)
        result = eval(code1)
        # if result:
        timeList = dict[timeEvt]
        shopTime = avgShopTime(timeList)
        # print shopTime
    except:
        print "Invalid input"
        return False,0
    return result,shopTime

