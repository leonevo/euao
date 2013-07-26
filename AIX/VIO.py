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

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)

"""
API for VIO Server
use telnet to execute command on VIOServer
"""

#VIO上建磁盘映射
def MakeVIODiskMap(VIOServerIP,
                   VIOServerUsername,
                   VIOServerPasswd,
                   rootvg_lun,
                   vhost_name,
                   VTD_name,
                   VIOServerPort=23,
                   VIOCmd_prompt='$',
                   OptionFromConfigFile=False):
    """
    变量名	注释	来源	举例
    rootvg_lun	VIOserver中磁盘的名称	从CMDB读入，对应字段“磁盘名称”	hdiskpower7
    vhost_name	VIOserver中vhost的名称	从CMDB读入，对应字段为“vhost名称”	Vhost7
    VTD_name	VIOserver中分区对应的VTD的名称	从CMDB读入，对应字段为“VTD名称”	Vioc7_rootvg
    
    Function: telnet to each VIOServer in VIOServerList, execute command
        command: mkvdev -vdev $rootvg_lun$ -vadapter $vhost_name$ -dev $VTD_name$

    
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if OptionFromConfigFile:
        VIOCmd_prompt=AIX_CommonDefinition.VIOServer_prompt
        VIOServerPort=AIX_CommonDefinition.VIOServer_port
    rootvg_lun_list=rootvg_lun.split(',')
    VTD_name_list=VTD_name.split(',')
    cmd_list=[]
    for i in range(len(rootvg_lun_list)):
        cmd_str=r'mkvdev -vdev %s -vadapter %s -dev %s' % (rootvg_lun_list[i],vhost_name,VTD_name_list[i])
        cmd_list_item=[cmd_str,VIOCmd_prompt,10]
        cmd_list.append(cmd_list_item)
    
    exit_code_list,output_list=BaseAdapter.ExecuteMultiCMDsviaTelnet(VIOServerIP,VIOServerUsername,VIOServerPasswd,cmd_list,port=23,cmd_prompt=VIOCmd_prompt)
    exit_code=0
    for code in exit_code_list:
        exit_code+=code
    output=''
    for item in output_list:
        output+=item[0]
    return exit_code,output
    #command_str=r'mkvdev -vdev %s -vadapter %s -dev %s' % (rootvg_lun,vhost_name,VTD_name)
    #return BaseAdapter.ExecuteCMDviaTelnet(VIOServerIP,VIOServerUsername,VIOServerPasswd,command_str,port=VIOServerPort,cmd_prompt=VIOCmd_prompt)
    
    
#VIO上删除磁盘映射
def RemoveVIODiskMap(VIOServerIP,
                   VIOServerUsername,
                   VIOServerPasswd,
                   VTD_name,
                   VIOServerPort=23,
                   VIOCmd_prompt='$',
                   OptionFromConfigFile=False):
    """
    变量名	注释	来源	举例
    VTD_name	VIOserver中分区对应的VTD的名称	从CMDB读入，对应字段为“VTD名称”	Vioc7_rootvg
    
    Function: telnet to VIOServer in VIOServerList, execute command
        command: $ rmvdev -dev $VTD_name$

    
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if OptionFromConfigFile:
        VIOCmd_prompt=AIX_CommonDefinition.VIOServer_prompt
        VIOServerPort=AIX_CommonDefinition.VIOServer_port
    command_str=r'rmvdev -vtd %s' % VTD_name
    myloger.debug('Remove vio disk map: %s' % command_str)
    
    #VTD_name is a list like: ces_vioc1_rootvg,ces_vioc1_datavg1,ces_vioc1_datavg2
    
    VTD_name_list=VTD_name.split(',')
    cmd_list=[]
    for item in VTD_name_list:
        cmd_str=r'rmvdev -vtd %s' % item
        cmd_list_item=[cmd_str,VIOCmd_prompt,10]
        cmd_list.append(cmd_list_item)
    
    
    exit_code_list,output_list=BaseAdapter.ExecuteMultiCMDsviaTelnet(VIOServerIP,VIOServerUsername,VIOServerPasswd,cmd_list,port=23,cmd_prompt=VIOCmd_prompt)
    exit_code=0
    for code in exit_code_list:
        exit_code+=code
    output=''
    for item in output_list:
        output+=item[0]
    return exit_code,output
    #return BaseAdapter.ExecuteCMDviaTelnet(VIOServerIP,VIOServerUsername,VIOServerPasswd,command_str,port=VIOServerPort,cmd_prompt=VIOCmd_prompt)