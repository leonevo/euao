#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import sys
root_dir=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_dir)
import CommonDefinition
import AdapterDefinition
sys.path.append(root_dir+AdapterDefinition.BaseAdapter_dir)
import BaseAdapter
import AIX_CommonDefinition
import datetime
#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)


"""
API for Check AIX action
use ssh to execute command on HMC
"""
def check_aix_status(server_ip,
                     username,
                     passwd,
                     protocal='telnet',
                     port=23,
                     cmd_prompt='#'):
    
    AIX_startup=False
    time_out_sec=10
    start_time=datetime.datetime.now()
    while not AIX_startup:
        if protocal=='telnet':
            exitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(server_ip,
                                                        username,
                                                        passwd,
                                                        'uname -a',
                                                        port=port,
                                                        cmd_prompt=cmd_prompt)
            if exitCode==0 and Output:
                myloger.debug('Server: %s is started-up.' % (server_ip))
                AIX_startup=True
            else:
                time_delta=datetime.datetime.now()-start_time
                if time_delta.total_seconds()>time_out_sec:
                    break
                else:
                    sleep(2)
            
            return exitCode,AIX_startup
            
        else:
            myloger.error('Error in checking %s status.' % server_ip)
            myloger.error('not support this protocal: %s' % protocal)
            exitCode=1
            return exitCode,AIX_startup