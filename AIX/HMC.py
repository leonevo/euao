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
API for HMC
use ssh to execute command on HMC
"""



#创建VIOClient分区
def CreateVIOClient(HMC_IP,
                    HMC_user,
                    HMC_passwd,
                    HMCServerName,
                    VIOClientName,
                    min_mem,
                    desired_mem,
                    max_mem,
                    min_procs,
                    desired_procs,
                    max_procs,
                    min_proc_units,
                    desired_proc_units,
                    max_proc_units,
                    virtual_eth_adapters,
                    virtual_scsi_adapter,
                    HMC_ssh_port=22,
                    OptionFromConfigFile=False):
    """
    变量名	注释	来源	举例
    ServerName	服务器名称	从CMDB读入，对应字段“服务器名”	Server-9117-MMA-SN06D6D82
    VIOClientName	分区名称	从CMDB读入，对应字段为“分区名”	vioc1_nnfh_mis（vioc_部门名称_应用简称）
    min_mem	分区最小内存数	默认值为1024	1024
    desired_mem	分区分配内存数	从CMDB读入，对应字段为“内存大小”	2048
    max_mem	分区最大内存数	默认值为32768	32768
    min_procs	分区最小逻辑CPU	默认值为1	1
    desired_procs	分区分配逻辑CPU	从CMDB读入，对应字段为“逻辑CPU数量”	2
    max_procs	分区最大逻辑CPU	默认值为16	16
    min_proc_units	分区最小物理CPU	默认值为0.1	0.1
    desired_proc_units	分区分配物理CPU	从CMDB读入，对应字段为“实际CPU量”	0.5
    max_proc_units	分区最大物理CPU	默认值为16	16
    virtual_eth_adapters	分区虚拟以太网卡	默认值为22/0/1///1,23/0/2///1
    virtual_scsi_adapter	分区虚拟scsi卡号	从CMDB读入，对应字段为“虚拟scsi卡”	23
        Command:
    mksyscfg -r lpar -m $ServerName$ -i "name=$VIOClientName$,profile_name=default,lpar_env=aixlinux,min_mem=$min_mem$,desired_mem=$desired_mem$,max_mem=$max_mem$,proc_mode=shared,min_procs=$min_procs$,desired_procs=$desired_procs$,max_procs=$max_procs$,min_proc_units=$min_proc_units$,desired_proc_units=$desired_proc_units$,max_proc_units=$max_proc_units$,sharing_mode=uncap,uncap_weight=128,auto_start=1,boot_mode=norm,max_virtual_slots=1000,\"virtual_eth_adapters=$virtual_eth_adapters$\",\"virtual_scsi_adapters=20/client//VIOserver1/$virtual_scsi_adapter$/1,21/client//VIOserver2/$virtual_scsi_adapter$/1\""
    
    return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
    else:
        HMC_ssh_port=int(HMC_ssh_port)
    command_str=r'mksyscfg -r lpar -m %s -i "name=%s,profile_name=default,lpar_env=aixlinux,min_mem=%s,desired_mem=%s,max_mem=%s,proc_mode=shared,min_procs=%s,desired_procs=%s,max_procs=%s,min_proc_units=%s,desired_proc_units=%s,max_proc_units=%s,sharing_mode=uncap,uncap_weight=128,auto_start=1,boot_mode=norm,max_virtual_slots=1000,\"virtual_eth_adapters=%s\",\"virtual_scsi_adapters=20/client//VIOserver1/%s/1,21/client//VIOserver2/%s/1\""' % (HMCServerName,VIOClientName,min_mem,desired_mem,max_mem,min_procs,desired_procs,max_procs,min_proc_units,desired_proc_units,max_proc_units,virtual_eth_adapters,virtual_scsi_adapter,virtual_scsi_adapter)
    
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=20)
    
#启动分区，开始安装
def LparNetboot(HMC_IP,
                HMC_user,
                HMC_passwd,
                NIMServerIP,
                VIOClientMgrIP,
                VIOClientMgrGateway,
                VIOClientName,
                HMCServerName,
                HMC_ssh_port=22,
                HMC_cmd_prompt='hscroot@localhost:~>',
                OptionFromConfigFile=False):
    """
    变量名	注释	来源	举例
    NIMServerIP	NIM服务器的IP地址	从CMDB读入	182.247.251.173
    VIOClientMgrIP	被安装系统的分区的管理IP地址	从CMDB读入，对应字段为“分区管理IP”	182.247.251.160
    VIOClientMgrGateway	被安装系统的分区的管理IP的网关	从CMDB读入，对应字段为“分区管理网关”	182.247.251.1
    VIOClientname	被安装系统的分区名字	从CMDB读入，对应字段为“分区名”	vioc1_test1
    HMCServername	被安装的分区所在的物理服务器	从CMDB读入，对应字段为“服务器名” Server-9117-MMA-SN06D6D82
    
    command: lpar_netboot -x -t ent -D -s auto -d auto -A -f -S $NIMServerIP$ -C $VIOClientMgrIP$ -G $VIOClientMgrGateway$ -i -K 255.255.255.0 $VIOClientname$ default $HMCServername$
    
    return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
       
    """
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
    command_str=r'lpar_netboot -x -t ent -D -s auto -d auto -A -f -S %s -C %s -G %s -i -K 255.255.255.0 %s default %s' % (NIMServerIP,VIOClientMgrIP,VIOClientMgrGateway,VIOClientName,HMCServerName)
    return BaseAdapter.ExecuteCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=1200,command_timeout=1200,cmd_prompt=HMC_cmd_prompt)
    
#启动分区
#2012.7.30
#test by leontan on 2012.12.19
def StartVIOClient(HMC_IP,
                   HMC_user,
                   HMC_passwd,
                   HMCServername,
                   VIOClientName,
                   profile_name,
                   HMC_ssh_port=22,
                   HMC_cmd_prompt='#',
                   OptionFromConfigFile=False):
    command_str='chsysstate -m %s -r lpar -o on -n %s -f %s' % (HMCServername,VIOClientName,profile_name)
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port)
    
#关闭分区
#2012.7.30
#test on 2012.12.19
def ShutdownVIOClient(HMC_IP,
                   HMC_user,
                   HMC_passwd,
                   HMCServername,
                   VIOClientName,
                   HMC_ssh_port=22,
                   HMC_cmd_prompt='#',
                   OptionFromConfigFile=False):
    command_str='chsysstate -m %s -r lpar -o shutdown -n %s --immed' % (HMCServername,VIOClientName)
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port)
    
    
#重启AIX分区
#test at 2012.12.19 by leontan
def RestartVIOClient(HMC_IP,
                      HMC_user,
                      HMC_passwd,
                      HMCServerName,
                      VIOClientName,
                      HMC_ssh_port=22,
                      HMC_cmd_prompt='#',
                      OptionFromConfigFile=False):
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
    
    command_str='chsysstate -m %s -r lpar -o shutdown -n %s --restart' % (HMCServerName,VIOClientName)
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=20)

#HMC上删除AIX分区
def RemoveVIOClient(HMC_IP,
                      HMC_user,
                      HMC_passwd,
                      HMCServerName,
                      VIOClientName,
                      HMC_ssh_port=22,
                      HMC_cmd_prompt='#',
                      OptionFromConfigFile=False):
    """
    HMC上执行：rmsyscfg -r lpar –m $ServerName$ -n $VIOClientName$
    
    HMCServerName	要删除的分区所在的物理服务器的名称	从CMDB读入，对应字段为“服务器名”	Server-9117-MMA-SN06D6D82
    LparName	要删除分区的分区名称	从CMDB读入，对应字段为“分区名”	vioc7_testdb1
    """
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
    
    command_str='rmsyscfg -r lpar -m %s -n %s' % (HMCServerName,VIOClientName)
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=20)

#HMC上关闭终端
def RemoveVTerm(HMC_IP,
                HMC_user,
                HMC_passwd,
                HMCServerName,
                VIOClientName,
                HMC_ssh_port=22,
                HMC_cmd_prompt='#',
                OptionFromConfigFile=False):
    """
     HMC上执行 rmvterm -m $HMCServername -p $VIOClientName
     
    """
    if OptionFromConfigFile:
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
    command_str='rmvterm -m %s -p %s' % (HMCServerName,VIOClientName)
    return BaseAdapter.ExecuteCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,cmd_prompt=HMC_cmd_prompt)
    #return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=20)
    
#减少VIOClient CPU
#leontan 2012.7.30 not tested
def ReduceVIOClientCPU(HMC_IP,
                       HMC_user,
                       HMC_passwd,
                       HMCServername,
                       VIOClientName,
                       CPU_count,
                       HMC_ssh_port=22,
                       HMC_cmd_prompt='#',
                       OptionFromConfigFile=False):
    """
    chhwres -r proc -m $HMCServerName -o r -p $VIOClientName --procs $CPU_Count
    """
    if OptionFromConfigFile:
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
    command_str='chhwres -r proc -m %s -o r -p %s --procs %d' % (HMCServerName,VIOClientName,CPU_count)
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(HMC_IP,HMC_user,HMC_passwd,command_str,port=HMC_ssh_port,connect_timeout=20)

#增加VIOClientCPU
# 2012.7.30 not tested
def AddVIOClientCPU(HMC_IP,
                    HMC_user,
                    HMC_passwd,
                    HMCServername,
                    VIOClientName,
                    profile_name,
                    Logical_CPU_Count,
                    Phycical_CPU_Count,
                    HMC_ssh_port=22,
                    HMC_cmd_prompt='#',
                    OptionFromConfigFile=False):
    """
    chhwres -r proc -m $HMCServerName -o r -p $VIOClientName --procs $CPU_Count
    """
    if OptionFromConfigFile:
        HMC_cmd_prompt=AIX_CommonDefinition.HMC_prompt
        HMC_ssh_port=AIX_CommonDefinition.HMC_port
    cmd1='chhwres -r proc -m %s -o a -p %s --porces %d --procunits %d --force' % (HMCServername,VIOClientName,Logical_CPU_Count,Phycical_CPU_Count)
    cmd2='chsyscfg -r prof -m %s -i name=%s,lpar_name=%s,desired_procs+=%d,desired_proc_units+=%d' % (HMCServername,profilename,VIOClientName,Logical_CPU_Count,Phycical_CPU_Count)
    cmds=[[cmd1,HMC_cmd_prompt,10],[cmd2,HMC_cmd_prompt,10]]
    return BaseAdapter.ExecuteMultiCMDsviaSSH2(HMC_IP,HMC_user,HMC_passwd,cmds,port=HMC_ssh_port,cmd_prompt=HMC_cmd_prompt)


if __name__ == '__main__':
    #test
    hmc_ip='182.247.251.247'
    hmc_user='hscroot'
    hmc_passwd='abc1234'
    AIX_ServerName='Server-9117-MMA-SN06D6D82'
    RemoveVTerm(hmc_ip,hmc_user,hmc_passwd,AIX_ServerName,VIOClientName='vioc7_test_leon_client',HMC_cmd_prompt='>')
    

   
    
    
