# -*- coding:utf-8 -*-
import os
import datetime


# 写log
def write(self):
    today_path = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)+"-log.txt" 
    #检测log文件是否存在   
    res = os.path.exists('./log/'+today_path)
    #创建一个当天日期的log
    if res==False:
        file = open('./log/'+today_path,'w')
        print("create logfile successs!!")
        file.close()
    #追加写入log，每天都更新
    with open('./log/'+today_path, 'a+',encoding='UTF-8') as f:
        d_time = "["+str(datetime.datetime.now())+"]:"
        f.write(d_time)
        f.write(str(self)+'\n')

