#-*- coding: utf-8 -*-
# here define some basic settings
import sys,os
import platform

#Web Server Setting
Tornado_port=8080

root_dir=os.path.dirname(__file__)
#current_path=sys.path[0]
#windows: '\', Linux: '/'
if platform.system()=='Windows':
    path_dir_sep='\\'
else:
    path_dir_sep='/'

#logFormat='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s - %(filename)s - $(module)s'
logFormat='%(asctime)s [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s'  
logFile=root_dir+path_dir_sep+'logs'+path_dir_sep+'euao.log'
logLevel='DEBUG'
loggerName='AdapterLog'

#log setting
import logging
#import logging.handlers
from logging import handlers

#logn层级设置
log_level=logging.DEBUG

myloger=logging.getLogger(loggerName)
myloger.setLevel(log_level)
sh=logging.StreamHandler()
fh=logging.FileHandler(logFile)
formatter = logging.Formatter(logFormat)
sh.setLevel(log_level)
fh.setLevel(log_level)

#生成RotatingFileHandler，设置文件大小为10M,编码为utf-8，最大文件个数为100个，如果日志文件超过100，则会覆盖最早的日志  
fh = logging.handlers.RotatingFileHandler(logFile,mode='a', maxBytes=1024*1024*1, backupCount=100, encoding="utf-8")


sh.setFormatter(formatter)
fh.setFormatter(formatter)
myloger.addHandler(sh)
myloger.addHandler(fh)

line_sep='\n'

#默认终端类型，对某些有终端类型要求的服务器在连接后需要对终端类型进行设置
DefaultTerminalType='vt100'

#simulation=True用于单机与ECMS联合调试，不实际操作IT基础架构环境，仅作时间及流程
#simulation=False
simulation=True
simulation_sleep_sec=0

"""
#用于aix环境设置
    生产环境设置 管理IP的网关为空，默认网关为服务IP的网关
    开发测试环境 默认网关为管理IP网关
"""
aix_default_gateway='service'
#aix_default_gateway='manage'
