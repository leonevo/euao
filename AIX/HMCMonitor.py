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
import re

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)

"""
API for HMC
use ssh to execute command on HMC
"""

def test():
    print 'ok'
    

def GetLPARStatus(HMC_IP,HMC_username,HMC_passwd,ServerName,port=22,**kwargs):
    """
    Get lpar status: running, not activate
    parameters:
        lpar_names: string, names seperated by comma
        lpar_ids:   string, id(s) seperated by comma
        if lpar_names and lpar_ids not provided, return all lpar status info
    return a dict, keys: name, id, status
    {
        'success':'True',
        'result':
            [
                {'name':'lpar1','lpar_id':'11','status':'running'},
                {'name':'lpar2','lpar_id':'12','status':'running'}
            ]
    }
    
    hmc command:
    lssyscfg -r lpar -m Server-9117-MMA-SN06D6D82 -F name,lpar_id,state --filter ""lpar_names=PIMS-UAT""
    lssyscfg -r lpar -m Server-9117-MMA-SN06D6D82 -F name,lpar_id,state --filter ""lpar_ids=15""
    response: vioc4_test,15,Not Activated
    """
    lpar_names=kwargs.get('lpar_names')
    lpar_ids=kwargs.get('lpar_ids')
    if lpar_names and lpar_ids:
        #can not provide both lpar_names and lpar_ids
        success=False
        info='can not provide both lpar_names and lpar_ids'
        result=[]
        myloger.error(info)
        result={'result': result, 'info':info, 'success': str(success)}
        return str(result)
    
    if lpar_names and not lpar_ids:
        cmd_str='lssyscfg -r lpar -m %s -F name,lpar_id,state --filter "\\"lpar_names=%s\\""' % (ServerName,lpar_names)
    if not lpar_names and lpar_ids:
        cmd_str='lssyscfg -r lpar -m %s -F name,lpar_id,state --filter "\\"lpar_ids=%s\\""' % (ServerName,lpar_ids)
    
    if not lpar_ids and not lpar_names:
        cmd_str='lssyscfg -r lpar -m %s -F name,lpar_id,state' % ServerName
            
    exit_code,cmd_result_list=BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_username,HMC_passwd,cmd_str,port=port,connect_timeout=20,return_list=True)
    if exit_code!=0:
        success=False
        info=str(cmd_result_list)
        result=[]
        myloger.error(info)
        result={'result': result, 'info':info, 'success': str(success)}
        return str(result)
    else:
        success=True
        key_list=[]
        try:
            for item in cmd_result_list:
                single_lpar_dict={}
                item_list=item.split(',')
                single_lpar_dict['name']=item_list[0]
                single_lpar_dict['lpar_id']=item_list[1]
                single_lpar_dict['status']=item_list[2]
                key_list.append(single_lpar_dict)
            result={'success':str(success),'info':'','result':key_list}
            return str(result)
        except Exception,e:
            info='Error in set GetLPARStatus result: %s' % e
            myloger.error(info)
            result={'success':'False','info':info,'result':[]}
            return str(result)
        
def GetAllLparStatus(HMC_IP,HMC_username,HMC_passwd,ServerNames_str,port=22,**kwargs):
    """
    ServerNames_str is a str of ServerName splitted by comma, like 'MMA-9917,MMA-9918'
    """
    
    #just for simulate, no server
    if CommonDefinition.simulation:
        result_list=[{'name':'lpar1','lpar_id':'11','status':'running'},{'name':'lpar2','lpar_id':'12','status':'running'}]
        return 0,str({'success':'True','info':'get all lpar status','result':result_list})
    
    result_list=[]
    ServerName_list=ServerNames_str.split(',')
    for server_item in ServerName_list:
        result_item=eval(GetLPARStatus(HMC_IP,HMC_username,HMC_passwd,server_item,port,**kwargs))
        if result_item.get('success')=='True':
            result_list+=result_item.get('result')
    
    if len(result_list)>0:
        result={'success':'True','info':'get all lpar status','result':result_list}
        return 0,str(result)
    else:
        result={'success':'False','info':'Error','result':[]}
        return 3,str(result)

def GetLPARInfo(HMC_IP,HMC_username,HMC_passwd,ServerName,port=22,**kwargs):
    print

def GetAIXServerInfo(HMC_IP,HMC_username,HMC_passwd,ServerName,port=22,**kwargs):
    """get AIX server
        configurable processing units(configurable_sys_proc_units),
        Available processing units(curr_avail_sys_proc_units),
        Conifgurable system memory(configurable_sys_mem, MB),
        Available memory(curr_avail_sys_mem, MB)
    
    hscroot@localhost:~> lslparutil -r sys -m Server-9117-MMA-SN06D6D82
time=06/13/2013 16:50:24,event_type=sample,resource_type=sys,sys_time=06/13/2013 16:46:06,state=Operating,configurable_sys_proc_units=16.0,configurable_sys_mem=131072,curr_avail_sys_proc_units=1.8,curr_avail_5250_cpw_percent=0.0,curr_avail_sys_mem=25344,sys_firmware_mem=7168,proc_cycles_per_second=512000000
    
    """
    if CommonDefinition.simulation:
        return {}
    cmd_str='lslparutil -r sys -m %s' % ServerName
    exit_code,cmd_result_list=BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_username,HMC_passwd,cmd_str,port=port,connect_timeout=30,return_list=True)
    if exit_code!=0:
        info='Error in issuing cmd %s to hmc' % cmd_str
        return {'success':'False','info':info,'result':''}
    else:
        cmd_result_str=cmd_result_list[0]
        myloger.debug('cmd_result: %s' % cmd_result_str)
        try:
            state=re.findall(r"state=(.+?),",cmd_result_str)[0]
            configurable_sys_proc_units=re.findall(r"configurable_sys_proc_units=(.+?),",cmd_result_str)[0]
            curr_avail_sys_proc_units=re.findall(r"curr_avail_sys_proc_units=(.+?),",cmd_result_str)[0]
            configurable_sys_mem=re.findall(r"configurable_sys_mem=(.+?),",cmd_result_str)[0]
            curr_avail_sys_mem=re.findall(r"curr_avail_sys_mem=(.+?),",cmd_result_str)[0]
            
            return {'server':ServerName,'configurable_sys_mem':configurable_sys_mem,'configurable_sys_proc_units':configurable_sys_proc_units,'curr_avail_sys_mem':curr_avail_sys_mem,'curr_avail_sys_proc_units':curr_avail_sys_proc_units}
        except Exception,e:
            myloger.error('Error in get regex result.')
            return {}
        
        
   
if __name__ == '__main__':
    ip='182.247.251.247'
    user='hscroot'
    passwd='abc1234'
    server_name='Server-9117-MMA-SN06D6D82'
    """
    print GetLPARStatus(ip,user,passwd,server_name,port=22,lpar_names='PIMS-UAT,Lpar3')
    print '----------------'
    print GetLPARStatus(ip,user,passwd,server_name,port=22,lpar_ids='6,7')
    print '----------------'
    print GetLPARStatus(ip,user,passwd,server_name,port=22)
    """
    print GetAIXServerInfo(ip,user,passwd,server_name)