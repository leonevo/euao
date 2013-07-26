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

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)


import datetime

import NIM
import VIO
import HMC
import AIX_CommonDefinition
from time import sleep

"""
API for AIX System
use telnet to execute command on AIX OS
"""

#执行简单命令
def ExecuteCMDviaTelnet(TargetServerIP,
                        TargetServerUsername,
                        TargetServerPasswd,
                        command,
                        TargetServerCmdPrompt='#'):
    return BaseAdapter.ExecuteCMDviaTelnet(TargetServerIP,
                                           TargetServerUsername,
                                           TargetServerPasswd,
                                           command,
                                           cmd_prompt=TargetServerCmdPrompt)
    
def ExecuteCMDviaSSH2(TargetServerIP,
                      TargetServerUsername,
                      TargetServerPasswd,
                      command):
    return BaseAdapter.ExecuteSimpleCMDviaSSH2(TargetServerIP,
                                               TargetServerUsername,
                                               TargetServerPasswd,
                                               command)
#issue 'cfgmgr' command to scan all pv in vioclient
def cfgmgr(TargetServerIP,
           TargetServerUsername,
           TargetServerPasswd,
           TargetServerCmdPrompt='#',
           TargetServerPort=23):
    cmd='cfgmgr'
    
    ExitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(TargetServerIP,
                                                    TargetServerUsername,
                                                    TargetServerPasswd,
                                                    cmd,
                                                    port=TargetServerPort,
                                                    cmd_prompt=TargetServerCmdPrompt,
                                                    log=True)
    return ExitCode,Output


#为分区配置服务IP
def ChangeVIOClientIP(VIOClientMgrIP,
                      VIOClientMgrGateway,
                      TargetServerUsername,
                      TargetServerPasswd,
                      VIOClientHostname,
                      VIOClientServiceIP,
                      VIOClientServiceGateway,
                      TargetServerPort=23,
                      TargetServerCmdPrompt='#',
                      OptionFromConfigFile=False):
    """
    变量名	注释	来源	举例
    VIOClientHostname	被安装系统的服务器主机名	从CMDB读入，对应字段为“分区主机名”	testhost
    VIOClientServiceIP	被安装系统的服务IP	从CMDB读入，对应字段为“分区服务IP”	192.168.1.123
    VIOClientServiceEthName	被安装系统的服务网卡	从CMDB读入，对应字段为“分区服务网卡”	en0
    VIOClientServiceGateway	被安装系统的服务网关	从CMDB读入，对应字段为“分区服务网关”	192.168.1.1
        
    
    Telnet to MgrIP:  /softinstall/mkdev_etherchannel.sh ent2 ent3
    Telnet to MgrIP:  /usr/sbin/mktcpip -h '$VIOClientHostname' -a $VIOclientServiceIP -m 255.255.255.0 -i en4 -g $VIOClientMgrGateway -A no -t N/A -s
    Telnet to ServiceIP: /softinstall/mkdev_etherchannel.sh ent0 ent1
    Telnet to ServiceIP: /usr/sbin/mktcpip -h '$VIOClientHostname' -a $VIOclientMgrIP -m 255.255.255.0 -i en5 -g $VIOClientMgrGateway -A no -t N/A -s
    
    return:
        exitCode:
            0: success
            1: connection error
            2: command error
        commandOutput: output
               
    
    """
    if OptionFromConfigFile:
        TargetServerPort=AIX_CommonDefinition.AIX_TelnetPort
        TargetServerCmdPrompt=AIX_CommonDefinition.AIX_Cmd_prompt
        TargetServerUsername=AIX_CommonDefinition.AIX_Default_Username
        TargetServerPasswd=AIX_CommonDefinition.AIX_Default_Passwd
        
    #cmd_str1='/softinstall/mkdev_etherchannel.sh ent2 ent3'
    #cmd_str1="""mkdev -c adapter -s pseudo -t ibm_ech -a adapter_names='ent2,ent3'"""
    cmd_str1='pwd'
    if CommonDefinition.aix_default_gateway=='service':
        #has service gateway, for production environment.
        cmd_str2='/usr/sbin/mktcpip -h %s -a %s -m 255.255.255.0 -i en1 -g %s -A no -t N/A -s \'\'' % (VIOClientHostname,VIOClientServiceIP,VIOClientServiceGateway)
    else:
        cmd_str2='/usr/sbin/mktcpip -h %s -a %s -m 255.255.255.0 -i en1 -A no -t N/A -s \'\'' % (VIOClientHostname,VIOClientServiceIP)
    #should be ServiceIP gateway
    #cmd_str3='/softinstall/mkdev_etherchannel.sh ent0 ent1'
    #cmd_str3="""mkdev -c adapter -s pseudo -t ibm_ech -a adapter_names='ent0,ent1'"""
    cmd_str3='pwd'
    #cmd_str4='/usr/sbin/mktcpip -h %s -a %s -m 255.255.255.0 -i en5 -g %s -A no -t N/A -s \'\'' % (VIOClientHostname,VIOClientMgrIP,VIOClientMgrGateway)

    if CommonDefinition.aix_default_gateway=='manage':
        cmd_str4='/usr/sbin/mktcpip -h %s -a %s -m 255.255.255.0 -i en0 -g %s -A no -t N/A -s \'\'' % (VIOClientHostname,VIOClientMgrIP,VIOClientMgrGateway)
    else:
        cmd_str4='/usr/sbin/mktcpip -h %s -a %s -m 255.255.255.0 -i en0 -A no -t N/A -s \'\'' % (VIOClientHostname,VIOClientMgrIP)
    
    """
    # skip this step. From 2013.1.23, do not make eth_channel
    ExitCode,Cmd_output=BaseAdapter.ExecuteCMDviaTelnet(VIOClientMgrIP,
                                                        TargetServerUsername,
                                                        TargetServerPasswd,
                                                        cmd_str1,
                                                        port=TargetServerPort,
                                                        cmd_prompt=TargetServerCmdPrompt,
                                                        get_exit_code=False)
    if ExitCode!=0:
        myloger.error("Error occured in ChangeVIOClientIP-step 1/4. TargetServer: %s, %s, %s. cmd: %s, output: %s" % (VIOClientHostname,VIOClientMgrIP,VIOClientServiceIP,cmd_str1,Cmd_output))
        return ExitCode,Cmd_output
    """
    
    ExitCode,Cmd_output=BaseAdapter.ExecuteCMDviaTelnet(VIOClientMgrIP,
                                                        TargetServerUsername,
                                                        TargetServerPasswd,
                                                        cmd_str2,
                                                        port=TargetServerPort,
                                                        cmd_prompt=TargetServerCmdPrompt,
                                                        get_exit_code=False)
    
    sleep(10)
    #change check method:
    ExitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(VIOClientServiceIP,
                                                    TargetServerUsername,
                                                    TargetServerPasswd,
                                                    'uname -a',
                                                    port=TargetServerPort,
                                                    cmd_prompt=TargetServerCmdPrompt,
                                                    log=True)
    if ExitCode!=0:
        myloger.error("Error occured in ChangeVIOClientIP-step 1/4. TargetServer: %s, %s, %s. cmd: %s, output: %s" % (VIOClientHostname,VIOClientMgrIP,VIOClientServiceIP,cmd_str2,Cmd_output))
        return ExitCode,Cmd_output
    
    """
    #skip this step. From 2013.1.23, do not make eth_channel
    ExitCode,Cmd_output=BaseAdapter.ExecuteCMDviaTelnet(VIOClientServiceIP,
                                                        TargetServerUsername,
                                                        TargetServerPasswd,
                                                        cmd_str3,
                                                        port=TargetServerPort,
                                                        cmd_prompt=TargetServerCmdPrompt,
                                                        get_exit_code=False)
    if ExitCode!=0:
        myloger.error("Error occured in ChangeVIOClientIP-step 3/4. TargetServer: %s, %s, %s. cmd: %s, output: %s" % (VIOClientHostname,VIOClientMgrIP,VIOClientServiceIP,cmd_str3,Cmd_output))
        return ExitCode,Cmd_output
    """      
    
    ExitCode,Cmd_output=BaseAdapter.ExecuteCMDviaTelnet(VIOClientServiceIP,
                                                        TargetServerUsername,
                                                        TargetServerPasswd,
                                                        cmd_str4,
                                                        port=TargetServerPort,
                                                        cmd_prompt=TargetServerCmdPrompt,
                                                        get_exit_code=False)
    if ExitCode!=0:
        myloger.error("Error occured in ChangeVIOClientIP-step 2/4. TargetServer: %s, %s, %s. cmd: %s, output: %s" % (VIOClientHostname,VIOClientMgrIP,VIOClientServiceIP,cmd_str4,Cmd_output))
        return ExitCode,Cmd_output
    
    myloger.info("Successfully ChangeVIOClientIP TargetServer: %s, %s, %s." % (VIOClientHostname,VIOClientMgrIP,VIOClientServiceIP))
    return ExitCode,'Successfully change VIO ClientIP'
    


#启动ITMAgent
def StartITMAgent(TargetServerIP,TargetServerUsername,TargetServerPasswd,StartCommand=r'/itm/bin/itmcmd agent start ux um'):
    """
    Start ITM Agent
    
    return:
        exitCode:
            0: success
            1: connection error
            2: command error
        commandOutput: output
    """
    
    return BaseAdapter.ExecuteCMDviaTelnet(TargetServerIP,
                                           TargetServerUsername,
                                           TargetServerPasswd,
                                           StartCommand,
                                           port=TargetServerPort)
    
    
#安装AIX操作系统一系列操作
def InstallAIX(spot,
            lpp_source,
            mksysb,
            ServerHostname,
            HMCServername,
            HMC_IP,
            HMC_username,
            HMC_passwd,
            TargetServerMgrIP,
            NIM_IP,
            NIM_username,
            NIM_passwd,
            VIOClientMgrGateway,
            VIOClientname,
            VIOClientServiceIP,
            VIOClientServiceGateway,
            HMC_ssh_port=22,
            HMC_cmd_prompt='>',
            NIM_port=23,
            NIM_prompt='#',
            TargetServerPort=23,
            TargetServerCmdPrompt='#',
            TargetServerUsername='root',
            TargetServerPasswd='root',
            OptionFromConfigFile=False):
    """
    1. NIMCreateClient
    2. NIM_bos_inst
    3. HMC Lpar netboot
    4. Config eth and Service IP
    """
    if OptionFromConfigFile:
        #step 1: NIM Create Client
        ExitCode,Output=NIM.NIMCreateClient(NIM_IP,
                                            NIM_username,
                                            NIM_passwd,
                                            TargetServerMgrIP,
                                            ServerHostname,
                                            OptionFromConfigFile=True)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM Create Client.' % (TargetServerMgrIP,ServerHostname)
            
            myloger.error(Msg)
            return ExitCode,Msg
        
        #step 2: NIM bost install
        ExitCode,Output=NIM.NIM_bos_inst(NIM_IP,
                                         NIM_username,
                                         NIM_passwd,
                                         spot,
                                         lpp_source,
                                         mksysb,
                                         ServerHostname,
                                         OptionFromConfigFile=True)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM bos_inst.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            return ExitCode,Msg
        #step 3: HMC Lpar net boot
        ExitCode,Output=HMC.LparNetboot(HMC_IP,
                                        HMC_username,
                                        HMC_passwd,
                                        NIM_IP,
                                        TargetServerMgrIP,
                                        VIOClientMgrGateway,
                                        VIOClientname,
                                        HMCServername,
                                        OptionFromConfigFile=True)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM bos_inst.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            return ExitCode,Msg
        #step 4: 
        #wait 20min for the AIX to boot up
        AIX_startup=False
        time_out_sec=40*60
        start_time=datetime.datetime.now()
        TargetServerUsername=AIX_CommonDefinition.AIX_Default_Username
        TargetServerPasswd=AIX_CommonDefinition.AIX_Default_Passwd
        while not AIX_startup:
            exitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(TargetServerMgrIP,
                                                            TargetServerUsername,
                                                            TargetServerPasswd,
                                                            'uname -a',
                                                            port=AIX_CommonDefinition.AIX_TelnetPort,
                                                            cmd_prompt=AIX_CommonDefinition.AIX_Cmd_prompt)
            if exitCode==0 and Output:
                myloger.debug('Server: %s, %s is started-up.' % (TargetServerMgrIP,VIOClientname))
                AIX_startup=True
            else:
                time_delta=datetime.datetime.now()-start_time
                if time_delta.total_seconds()>time_out_sec:
                    break
                else:
                    sleep(10)
                    
        if AIX_startup:
            ExitCode,Output=ChangeVIOClientIP(TargetServerMgrIP,
                                              VIOClientMgrGateway,
                                              TargetServerUsername,
                                              TargetServerPasswd,
                                              ServerHostname,
                                              VIOClientServiceIP,
                                              VIOClientServiceGateway,
                                              OptionFromConfigFile=True)
            if ExitCode==0:
                ExitCode,Output=cfgmgr(TargetServerMgrIP,TargetServerUsername,TargetServerPasswd)
                Msg='Server %s, %s installation completed.' % (TargetServerMgrIP,VIOClientname)
                myloger.info(Msg)
                return ExitCode,Msg
            else:
                Msg='Server %s, %s Error in Manage/Server IP Configuration.'
                myloger.error(Msg)
                return ExitCode,Msg
        else:
            Msg='Server: %s, %s fail to boot up in 20 min. Telnet can not connect.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            ExitCode=3
            return ExitCode,Msg
    else:
        #step 1: NIM Create Client
        ExitCode,Output=NIM.NIMCreateClient(NIM_IP,
                                            NIM_username,
                                            NIM_passwd,
                                            TargetServerMgrIP,
                                            ServerHostname,
                                            NIM_port=NIM_port,
                                            NIM_prompt=NIM_prompt)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM Create Client.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            return ExitCode,Msg
        
        #step 2: NIM bost install
        ExitCode,Output=NIM.NIM_bos_inst(NIM_IP,
                                         NIM_username,
                                         NIM_passwd,
                                         spot,
                                         lpp_source,
                                         mksysb,
                                         ServerHostname,
                                         NIM_port=NIM_port,
                                         NIM_prompt=NIM_prompt)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM bos_inst.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            return ExitCode,Msg
        #step 3: HMC Lpar net boot
        ExitCode,Output=HMC.LparNetboot(HMC_IP,
                                        HMC_username,
                                        HMC_passwd,
                                        NIM_IP,
                                        TargetServerMgrIP,
                                        VIOClientMgrGateway,
                                        VIOClientname,
                                        HMCServername,
                                        HMC_ssh_port=HMC_ssh_port,
                                        HMC_cmd_prompt=HMC_cmd_prompt)
        if ExitCode!=0:
            Msg='Server %s, %s Error in NIM bos_inst.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            return ExitCode,Msg
        
        #step 4: 
        #wait 20min for the AIX to boot up
        AIX_startup=False
        time_out_sec=20*60
        start_time=datetime.datetime.now()
        while not AIX_startup:
            exitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(TargetServerMgrIP,
                                                            TargetServerUsername,
                                                            TargetServerPasswd,
                                                            'uname -a',
                                                            port=TargetServerPort,
                                                            cmd_prompt=TargetServerCmdPrompt,
                                                            log=False)
            if exitCode==0 and Output:
                myloger.info('Server: %s, %s is started-up.' % (TargetServerMgrIP,VIOClientname))
                AIX_startup=True
            else:
                time_delta=datetime.datetime.now()-start_time
                if time_delta.total_seconds()>time_out_sec:
                    break
                else:
                    sleep(10)
                    
        if AIX_startup:
            ExitCode,Output=ChangeVIOClientIP(TargetServerMgrIP,
                                              VIOClientMgrGateway,
                                              TargetServerUsername,
                                              TargetServerPasswd,
                                              ServerHostname,
                                              VIOClientServiceIP,
                                              VIOClientServiceGateway,
                                              TargetServerPort=TargetServerPort,
                                              TargetServerCmdPrompt=TargetServerCmdPrompt)
            if ExitCode==0:
                Msg='Server %s, %s installation completed.' % (TargetServerMgrIP,VIOClientname)
                myloger.info(Msg)
                return ExitCode,Msg
            else:
                Msg='Server %s, %s Error in Manage/Server IP Configuration.' % (TargetServerMgrIP,VIOClientname)
                myloger.error(Msg)
                myloger.debug('Exitcode: %d, ouput: %s' % (ExitCode,Output))
                return ExitCode,Msg
        else:
            Msg='Server: %s, %s fail to boot up. Telnet can not connect.' % (TargetServerMgrIP,VIOClientname)
            myloger.error(Msg)
            ExitCode=3
            return ExitCode,Msg

def ChangeAIXPwd(TargetServerIP,
                 Username,
                 OldPasswd,
                 NewPasswd,
                 o_TargetServerPrompt,
                 o_TargetServerPort,
                 OptionFromConfigFile=False):
    """
    更改AIX用户密码
    """
    if OptionFromConfigFile:
        o_TargetServerPort=AIX_CommonDefinition.AIX_TelnetPort
        o_TargetServerPrompt=AIX_CommonDefinition.AIX_Cmd_prompt
    """
    依次执行以下3条命令：passwd, NewPasswd, NewPasswd,
    """
    commands=[['passwd','password:',5,NewPasswd,'password:',5,NewPasswd,'$',5]]
    return BaseAdapter.ExecuteMultiCMDsviaTelnet(TargetServerIP,
                                                 Username,
                                                 OldPasswd,
                                                 commands)
            
#创建AIX分区，并划磁盘，装系统，配网卡，配IP,
def CreateWholeAIXVIOClient(HMC_IP,
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
                            VIOServerIP_1,
                            VIOServerUsername_1,
                            VIOServerPasswd_1,
                            VIOServerIP_2,
                            VIOServerUsername_2,
                            VIOServerPasswd_2,
                            rootvg_lun,
                            vhost_name,
                            VTD_name,
                            NIM_IP,
                            NIM_username,
                            NIM_passwd,
                            ClientMgrIP,
                            ServerHostName,
                            spot,
                            lpp_source,
                            mksysb,
                            HMC_username,
                            HMC_passwd,
                            VIOClientMgrGateway,
                            VIOClientServiceIP,
                            VIOClientServiceGateway,
                            TargetServerUsername,
                            TargetServerPasswd,
                            TargetServerPort=23,
                            TargetServerCmdPrompt='#',
                            HMC_ssh_port=22,
                            HMC_cmd_prompt='hscroot@localhost:~>',
                            VIOServerPort_1=23,
                            VIOCmd_prompt_1='$',
                            VIOServerPort_2=23,
                            VIOCmd_prompt_2='$',
                            NIM_port=23,
                            NIM_prompt='#',):
                            
    myloger.info('Begin to Install whole aix vioclient....')
    myloger.info('1. create vioclient')
    # 1. create vio client on HMC
    exit_code,output=HMC.CreateVIOClient(HMC_IP, HMC_username, HMC_passwd, HMCServerName, VIOClientName, min_mem, desired_mem, max_mem, min_procs, desired_procs, max_procs, min_proc_units, desired_proc_units, max_proc_units, virtual_eth_adapters, virtual_scsi_adapter, HMC_ssh_port)
    
    myloger.info('create vioclient result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in create vioclient.'
        myloger.error(msg)
        return 1,msg
    
    myloger.info('2. make vio disk map on vioserver_1')
    #2. mkvdev on 2 vio server
    exit_code,output=VIO.MakeVIODiskMap(VIOServerIP_1,
                   VIOServerUsername_1,
                   VIOServerPasswd_1,
                   rootvg_lun,
                   vhost_name,
                   VTD_name,
                   VIOServerPort_1,
                   VIOCmd_prompt_1)
    
    myloger.info('make vio disk map on vioserver_1 result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in making vio disk map on vioserver_1.'
        myloger.error(msg)
        return 1,msg
    
    exit_code,output=VIO.MakeVIODiskMap(VIOServerIP_2,
                   VIOServerUsername_2,
                   VIOServerPasswd_2,
                   rootvg_lun,
                   vhost_name,
                   VTD_name,
                   VIOServerPort_2,
                   VIOCmd_prompt_2)
    
    myloger.info('make vio disk map on vioserver_2 result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in making vio disk map on vioserver_1.'
        myloger.error(msg)
        return 1,msg
    
    #3. Install AIX OS
    myloger.info('3. Install AIX OS....')
    exit_code,output=InstallAIX(spot,
                            lpp_source,
                            mksysb,
                            ServerHostName,
                            HMCServerName,
                            HMC_IP,
                            HMC_username,
                            HMC_passwd,
                            ClientMgrIP,
                            NIM_IP,
                            NIM_username,
                            NIM_passwd,
                            VIOClientMgrGateway,
                            VIOClientName,
                            VIOClientServiceIP,
                            VIOClientServiceGateway,
                            HMC_ssh_port,
                            HMC_cmd_prompt,
                            NIM_port,
                            NIM_prompt,
                            TargetServerPort=23,
                            TargetServerCmdPrompt='#',
                            TargetServerUsername='root',
                            TargetServerPasswd='root')
    
    myloger.info('Install AIX OS result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in installing aix os.'
        myloger.error(msg)
        return 1,msg
    msg='Install whole aix complete!'
    myloger.info(msg)
    return 0,msg
                    
def RemoveWholeAIXVIOClient(HMC_IP,
                            HMC_user,
                            HMC_passwd,
                            HMCServerName,
                            VIOClientName,
                            HMC_ssh_port,
                            HMC_cmd_prompt,
                            NIM_IP,
                            NIM_username,
                            NIM_passwd,
                            ServerHostName,
                            NIM_port,
                            NIM_prompt,
                            VIOServerIP_1,
                            VIOServerUsername_1,
                            VIOServerPasswd_1,
                            VTD_name,
                            VIOServerPort_1,
                            VIOCmd_prompt_1,
                            VIOServerIP_2,
                            VIOServerUsername_2,
                            VIOServerPasswd_2,
                            VIOServerPort_2,
                            VIOCmd_prompt_2):
    
    #1. remove vterm from HMC, if any
    step_msg='remove vterm from HMC.'
    myloger.info('1. %s' % step_msg)
    exit_code,output=HMC.RemoveVTerm(HMC_IP,
                                    HMC_user,
                                    HMC_passwd,
                                    HMCServerName,
                                    VIOClientName,
                                    HMC_ssh_port,
                                    HMC_cmd_prompt)
    if exit_code!=0:
        err_msg='Error in step 1 %s' % step_msg
        myloger.error(err_msg)
        return 1,err_msg

    #2, shutdown lpar, if it is activate
    step_msg='2. shutdown lpar'
    myloger.info(step_msg)
    exit_code,output=HMC.ShutdownVIOClient(HMC_IP,HMC_user,HMC_passwd,HMCServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt)
    
    if exit_code!=0:
        err_msg='Error in step %s' % step_msg
        myloger.error(err_msg)
        return 1,err_msg
    
    #3, NIM remove client
    step_msg='3, NIM remove client'
    myloger.info(step_msg)
    exit_code,output=NIM.NIMRemoveClient(NIM_IP,NIM_username,NIM_passwd,ServerHostName,NIM_port,NIM_prompt)
    if exit_code!=0:
        err_msg='Error in step %s' % step_msg
        myloger.error(err_msg)
        return 1,err_msg
    
    #4, remove vioclient from HMC
    #wait for the vioclient completely shutdown
    sleep(10)
    
    step_msg='4, remove vioclient from HMC'
    myloger.info(step_msg)
    exit_code,output=HMC.RemoveVIOClient(HMC_IP,HMC_user,HMC_passwd,HMCServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt)
    if exit_code!=0:
        err_msg='Error in step %s' % step_msg
        myloger.error(err_msg)
        return 1,err_msg
    
    #5, remove vio disk map
    step_msg='5, remove vio disk map'
    myloger.info(step_msg)
    exit_code,output=VIO.RemoveVIODiskMap(VIOServerIP_1,VIOServerUsername_1,VIOServerPasswd_1,VTD_name,VIOServerPort_1,VIOCmd_prompt_1)
    if exit_code!=0:
        err_msg='Error in step %s, vioserver1' % step_msg
        myloger.error(err_msg)
        return 1,err_msg
    
    exit_code,output=VIO.RemoveVIODiskMap(VIOServerIP_2,VIOServerUsername_2,VIOServerPasswd_2,VTD_name,VIOServerPort_2,VIOCmd_prompt_2)
    if exit_code!=0:
        err_msg='Error in step %s, vioserver1' % step_msg
        myloger.error(err_msg)
        return 1,err_msg
    
    succeed_msg='Remove %s complete!' % VIOClientName
    myloger.info(succeed_msg)
    return 0,succeed_msg

#relocate vioclient to another server in the same cluster    
def Relocate_vioclient(original_server_status,
                      VIOServerIP_1,
                      VIOServerUsername_1,
                      VIOServerPasswd_1,
                      VIOServerPort_1,
                      VIOCmd_prompt_1,
                      VIOServerIP_2,
                      VIOServerUsername_2,
                      VIOServerPasswd_2,
                      VIOServerPort_2,
                      VIOCmd_prompt_2,
                      VTD_name,
                      rootvg_lun,
                      vhost_name,
                      HMC_IP,
                      HMC_user,
                      HMC_passwd,
                      original_ServerName,
                      target_ServerName,
                      VIOClientName,
                      profile_name,
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
                      vioclient_mgr_ip,
                      vioclient_username,
                      vioclient_passwd,
                      HMC_ssh_port,
                      HMC_cmd_prompt,
                      Target_server_VIOServerIP_1,
                      Target_server_VIOServerUsername_1,
                      Target_server_VIOServerPasswd_1,
                      Target_server_VIOServerPort_1,
                      Target_server_VIOCmd_prompt_1,
                      Target_server_VIOServerIP_2,
                      Target_server_VIOServerUsername_2,
                      Target_server_VIOServerPasswd_2,
                      Target_server_VIOServerPort_2,
                      Target_server_VIOCmd_prompt_2):
                      
    """
    ======迁移=========================
1.HMC上的P750-1删除分区
2.P750-1的两台Target_server_Target_server_VIO上删除磁盘映射
  rmvdev -vtd voic2_rootvg
3.如果有数据盘
  循环执行rmvdev

4.HMC上执行,P750-2上
mksyscfg -r lpar -m Server-8233-E8B-SN06A59FR -i "name=vioc2_mrgtest,profile_name=default,lpar_env=aixlinux,min_mem=1024,desired_mem=2048,max_mem=32768,proc_mode=shared,min_procs=1,desired_procs=2,max_procs=16,min_proc_units=0.1,desired_proc_units=1.0,max_proc_units=16,sharing_mode=uncap,uncap_weight=128,auto_start=1,boot_mode=norm,max_virtual_slots=1000,\"virtual_eth_adapters=22/0/1///1,23/0/2///1,24/0/11///1,25/0/12///1\",\"virtual_scsi_adapters=20/client//VIOSERVER1/9/1,21/client//VIOSERVER2/9/1\""

5.P750-2对应的两台VIO Server上
mkvdev -vdev hdiskpower3 -vadapter vhost2 -dev voic2_rootvg

6.如果有数据盘
  循环执行mkvdev
    """
    # 1. umount all hdisk from original hmc if the server is still running
    if original_server_status=='off':
        step_msg='1(pre): umount all hdisk from original hmc if the server is still running'
        myloger.info(step_msg)
        exit_code,output=VIO.RemoveVIODiskMap(VIOServerIP_1,VIOServerUsername_1,VIOServerPasswd_1,VTD_name,VIOServerPort_1,VIOCmd_prompt_1)
        if exit_code!=0:
            err_msg='Error in step %s, vioserver1' % step_msg
            myloger.error(err_msg)
            result={'Message':err_msg}
            return 1,str(result)
        
        exit_code,output=VIO.RemoveVIODiskMap(VIOServerIP_2,VIOServerUsername_2,VIOServerPasswd_2,VTD_name,VIOServerPort_2,VIOCmd_prompt_2)
        if exit_code!=0:
            err_msg='Error in step %s, vioserver1' % step_msg
            myloger.error(err_msg)
            result={'Message':err_msg}
            return 1,str(result)
    
    # 2. make new vioclient in ther target server from hmc
    HMC.CreateVIOClient(HMC_IP,
                    HMC_user,
                    HMC_passwd,
                    target_ServerName,
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
                    HMC_ssh_port)
    
    # 3. mount all hdisk in the target_server's vio server
    exit_code,output=VIO.MakeVIODiskMap(Target_server_VIOServerIP_1,
                   Target_server_VIOServerUsername_1,
                   Target_server_VIOServerPasswd_1,
                   rootvg_lun,
                   vhost_name,
                   VTD_name,
                   Target_server_VIOServerPort_1,
                   Target_server_VIOCmd_prompt_1)
    
    myloger.info('make vio disk map on vioserver_1 result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in making vio disk map on vioserver_1.'
        myloger.error(msg)
        result={'Message':msg}
        return 1,str(result)
    
    exit_code,output=VIO.MakeVIODiskMap(Target_server_VIOServerIP_2,
                   Target_server_VIOServerUsername_2,
                   Target_server_VIOServerPasswd_2,
                   rootvg_lun,
                   vhost_name,
                   VTD_name,
                   Target_server_VIOServerPort_2,
                   Target_server_VIOCmd_prompt_2)
    
    myloger.info('make vio disk map on vioserver_2 result: %d, %s' % (exit_code,output))
    if exit_code!=0:
        msg='error in making vio disk map on vioserver_1.'
        myloger.error(msg)
        result={'Message':msg}
        return 1,str(result)
    # 4. power on the new vioclient
    HMC.StartVIOClient(HMC_IP,HMC_user,HMC_passwd,target_ServerName,VIOClientName,profile_name,HMC_ssh_port,HMC_cmd_prompt)
    
    #check if the vioclient startup succeed.
    
    #wait 20min for the AIX to boot up
    AIX_startup=False
    time_out_sec=20*60
    start_time=datetime.datetime.now()
    TargetServerUsername=AIX_CommonDefinition.AIX_Default_Username
    TargetServerPasswd=AIX_CommonDefinition.AIX_Default_Passwd
    while not AIX_startup:
        exitCode,Output=BaseAdapter.ExecuteCMDviaTelnet(vioclient_mgr_ip,
                                                        vioclient_username,
                                                        vioclient_passwd,
                                                        'uname -a',
                                                        port=AIX_CommonDefinition.AIX_TelnetPort,
                                                        cmd_prompt=AIX_CommonDefinition.AIX_Cmd_prompt)
        if exitCode==0 and Output:
            myloger.debug('Server: %s, %s is started-up.' % (vioclient_mgr_ip,VIOClientName))
            AIX_startup=True
        else:
            time_delta=datetime.datetime.now()-start_time
            if time_delta.total_seconds()>time_out_sec:
                break
            else:
                sleep(10)
                
    if AIX_startup:
        # 5. delete the original vioclient
        exitCode,Output=HMC.RemoveVIOClient(HMC_IP,HMC_user,HMC_passwd,original_ServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt)
        if exitCode==0 and Output:
            msg='VIOClient %s has successfully been relocated to Server %s.' % (VIOClientName,target_ServerName)
            result={'vioclient':VIOClientName,'target_server':target_ServerName,'Message':msg}
            return 0,str(result)
        else:
            msg='Error in step 5: remove vioclient:%s from orignal server' % VIOClientName
            myloger.error(msg)
            result={'Message':msg,'output':Output}
            return 1,str(result)
    else:
        msg='VIOClient %s fails to startup after being relocated.' % VIOClientName
        myloger.info(msg)
        result={'Message':msg}
        return 1,str(result)
        
    
    

if __name__ == '__main__':
    print 'just for test'
    
