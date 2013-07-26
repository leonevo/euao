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

"""
API for NIM Server
use telnet to execute command on NIM Server
"""

#创建Client
def NIMCreateClient(NIM_IP,
                    NIM_username,
                    NIM_passwd,
                    ClientMgrIP,
                    ServerHostName,
                    NIM_port=23,
                    NIM_prompt='#',
                    OptionFromConfigFile=True):
    """
   变量名	注释	来源	举例
ClientMgrIP	被安装系统的分区管理IP	从CMDB读入，对应字段“分区管理IP”	182.247.251.159
ServerHostName	被安装系统的主机名称	从CMDB读入，对应字段为“分区主机名”	ZH-icsdb1
 
    command:
        /home/NIM_CreateClient.sh "ClientMgrIP" "ServerHostName"
    """
    if OptionFromConfigFile:
        NIM_prompt=AIX_CommonDefinition.NIM_prompt
        NIM_port=AIX_CommonDefinition.NIM_port
    command_str=r'/home/NIM_CreateClient.sh "%s" "%s"' % (ClientMgrIP,ServerHostName)
    return BaseAdapter.ExecuteCMDviaTelnet(NIM_IP,NIM_username,NIM_passwd,command_str,port=NIM_port,cmd_prompt=NIM_prompt)

#NIM删除VIOClient
def NIMRemoveClient(NIM_IP,
                    NIM_username,
                    NIM_passwd,
                    ServerHostName,
                    NIM_port=23,
                    NIM_prompt='#',
                    OptionFromConfigFile=True):
    """
    NIMServer上执行：删除Client的脚本
    En：/home/NIM_DeleteClient.sh $ServerHostName
    ServerHostName	要删除的分区的主机名	从CMDB读入，对应字段为“分区主机名”	ZH-testdb1
    """
    if OptionFromConfigFile:
        NIM_prompt=AIX_CommonDefinition.NIM_prompt
        NIM_port=AIX_CommonDefinition.NIM_port
    command_str='/home/NIM_DeleteClient.sh %s' % ServerHostName
    return BaseAdapter.ExecuteCMDviaTelnet(NIM_IP,NIM_username,NIM_passwd,command_str,port=NIM_port,cmd_prompt=NIM_prompt)
    
    
#发起系统安装命令
def NIM_bos_inst(NIM_IP,NIM_username,NIM_passwd,spot,Lpp_source,mksysb,ServerHostname,NIM_port=23,NIM_prompt='#',OptionFromConfigFile=True):
    """
    变量名	注释	来源	举例
    spot	被安装介质的spot	从CMDB读入，对应字段“spot资源”	AIX5307spot
    Lpp_source	被安装介质的lpp source	从CMDB读入，对应字段为“lpp资源”	AIX5307standard
    mksysb	被安装介质的模板	从CMDB读入，对应字段为“mksysb资源”	nimmmksysb
    ServerHostname	被安装系统的主机名	从CMDB读入，对应字段为“分区主机名”	ZH-icsdb1

    command:
    nim -o bos_inst \
    -a source=mksysb \
    -a spot=$spot$ \
    -a lpp_source=$lpp_source$ \
    -a mksysb=$mksysb$ \
    -a bosinst_data=bosinst_data_all\
    -a boot_client=no \
    $ServerHostname$


    return:
    exitCode:
        0: success
        1: connection error
        2: command error
    commandOutput: output
    """
    if OptionFromConfigFile:
        NIM_prompt=AIX_CommonDefinition.NIM_prompt
        NIM_port=AIX_CommonDefinition.NIM_port
    command_str=r'nim -o bos_inst -a source=mksysb -a spot=%s -a lpp_source=%s -a mksysb=%s -a bosinst_data=bosinst_data_all -a boot_client=no %s' % (spot,Lpp_source,mksysb,ServerHostname)
    return BaseAdapter.ExecuteCMDviaTelnet(NIM_IP,NIM_username,NIM_passwd,command_str,port=NIM_port,cmd_prompt=NIM_prompt)
    
