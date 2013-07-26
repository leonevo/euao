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

from tornadows import soaphandler
from tornadows import xmltypes
from tornadows.complextypes import ComplexType
from tornadows.soaphandler  import webservice
import AIX
import HMC
import NIM
import VIO
import AIX_Check
import HMCMonitor
import AIX_CommonDefinition
from time import ctime,sleep
from EThread import EThread
from ReturnTypes import TelnetReturnType,SSHReturnType,CommandReturnType
import time

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)

"""
web service class for control AIX
"""

class ControlAIX(soaphandler.SoapHandler):
    """
    use functions in AIX/HMC/NIM/VIO to operate aix
    """
    ServiceThread={}

    @webservice(_params=str,_returns=CommandReturnType)
    def GetCommandResponse(self,ThreadID):
        """
        Telnet/SSH return the ExitCode and CommandOutput
        use the ThreadID to find the return result. and clear the record in hash.
        """
        r=CommandReturnType()
        if self.ServiceThread.has_key(ThreadID):
            if self.ServiceThread[ThreadID].isAlive():
                r.ExitCode=2
                r.CommandOutput='Running'
            else:
                # if GetStatus return Complete, thread will be delete so that you can't use GetResult
                r.ExitCode,r.CommandOutput=self.ServiceThread[ThreadID].GetResult()
                del self.ServiceThread[ThreadID]
        else:
            r.ExitCode=4
            r.CommandOutput='Wrong thread id.'
        return r


    @webservice(_params=[str,str,str,str,str,str,str],_returns=str)
    def TelnetCmd(self,host,user,passwd,command,cmd_prompt='#'):
        r=TelnetReturnType()
        t=EThread(AIX.ExecuteCMDviaTelnet,(host,user,passwd,command,cmd_prompt))
        #r.ExitCode,r.CommandOutput=AIX.ExecuteCMDviaTelnet(host,user,passwd,command)

        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,str,str,str],_returns=str)
    def SSHCmd(self,host,user,passwd,command):
        r=SSHReturnType()
        t=EThread(AIX.ExecuteCMDviaSSH2,(host,user,passwd,command))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,int,str],_returns=str)
    def CreateVIOClient(self,
                        HMC_IP,
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
                        o_HMC_ssh_port=22,
                        OptionFromConfigFile=True):
        r=SSHReturnType()
        if OptionFromConfigFile:
            t=EThread(HMC.CreateVIOClient,
                  (HMC_IP,HMC_user,HMC_passwd,HMCServerName,VIOClientName,min_mem,desired_mem,max_mem,min_procs,desired_procs,max_procs,min_proc_units,desired_proc_units,max_proc_units,virtual_eth_adapters,                   virtual_scsi_adapter,'','True'))

        else:
            t=EThread(HMC.CreateVIOClient,
                  (HMC_IP,HMC_user,HMC_passwd,HMCServerName,VIOClientName,min_mem,desired_mem,max_mem,min_procs,desired_procs,max_procs,min_proc_units,desired_proc_units,max_proc_units,virtual_eth_adapters,                   virtual_scsi_adapter,HMC_ssh_port))

        tid=t.GetThreadID()

        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,str,str,int,str,str],_returns=str)
    def MakeVIODiskMap(self,
                       VIOServerIP,
                       VIOServerUsername,
                       VIOServerPasswd,
                       rootvg_lun,
                       vhost_name,
                       VTD_name,
                       o_VIOServerPort=23,
                       o_VIOCmd_prompt='$',
                       OptionFromConfigFile=False):
        """
    变量名   注释  来源  举例
    rootvg_lun  VIOserver中磁盘的名称     从CMDB读入，对应字段“磁盘名称”  hdiskpower7
    vhost_name  VIOserver中vhost的名称      从CMDB读入，对应字段为“vhost名称”        Vhost7
    VTD_name    VIOserver中分区对应的VTD的名称 从CMDB读入，对应字段为“VTD名称”  Vioc7_rootvg

    Function: telnet to each VIOServer in VIOServerList, execute command
        command: mkvdev -vdev $rootvg_lun$ -vadapter $vhost_name$ -dev $VTD_name$
        """
        if OptionFromConfigFile:
            t=EThread(VIO.MakeVIODiskMap,
                  (VIOServerIP,VIOServerUsername,VIOServerPasswd,rootvg_lun,vhost_name,VTD_name,'','','True')
                 )
        else:
            t=EThread(VIO.MakeVIODiskMap,
                  (VIOServerIP,VIOServerUsername,VIOServerPasswd,rootvg_lun,vhost_name,VTD_name,VIOServerPort,VIOCmd_prompt)
                 )
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,int,str,str],_returns=str)
    def RemoveVIODiskMap(self,
                         VIOServerIP,
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
        r=TelnetReturnType()
        if OptionFromConfigFile:
            t=EThread(VIO.RemoveVIODiskMap,
                  (VIOServerIP,VIOServerUsername,VIOServerPasswd,VTD_name,'','','True')
                 )
        else:
            t=EThread(VIO.RemoveVIODiskMap,
                  (VIOServerIP,VIOServerUsername,VIOServerPasswd,VTD_name,VIOServerPort,VIOCmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,int,int,str,int,str,str,str,str],_returns=str)

    #安装AIX操作系统一系列操作
    def InstallAIX(self,
            spot,
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
            o_HMC_ssh_port=22,
            o_NIM_port=22,
            o_NIM_prompt='#',
            o_TargetServerPort=23,
            o_TargetServerCmdPrompt='#',
            o_TargetServerUsername='root',
            o_TargetServerPasswd='root',
            OptionFromConfigFile=False):

        r=TelnetReturnType()
        if OptionFromConfigFile:
            t=EThread(AIX.InstallAIX,
                  (spot,
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
                    0,
                    0,
                    '',
                    0,
                    '',
                    '',
                    '',
                    'True'))
        else:
            t=EThread(AIX.InstallAIX,
                (spot,
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
                HMC_ssh_port,
                NIM_port,
                NIM_prompt,
                TargetServerPort,
                TargetServerCmdPrompt,
                TargetServerUsername,
                TargetServerPasswd))

        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    
    @webservice(_params=[str,str,str,str,str,int,str],_returns=str)
    def ChangeAIXPasswd(self,
                        TargetServerIP,
                        Username,
                        OldPasswd,
                        NewPasswd,
                        o_TargetServerPrompt,
                        o_TargetServerPort,
                        OptionFromConfigFile=False):
        if OptionFromConfigFile:
            t=EThread(AIX.ChangeAIXPwd,(TargetServerIP,Username,OldPasswd,NewPasswd,'',0,True))
        else:
            t=EThread(AIX.ChangeAIXPwd,(TargetServerIP,Username,OldPasswd,NewPasswd,o_TargetServerPrompt,o_TargetServerPort))
        
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    
    
    
    #创建/安装AIX系统完整过程
    @webservice(_params=[str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,int,str,int,str,int,str,int,str,int,str],_returns=str)
    def InstallWholeAIX(self,
                        HMC_IP,
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
                        TargetServerPort,
                        TargetServerCmdPrompt,
                        HMC_ssh_port,
                        HMC_cmd_prompt,
                        VIOServerPort_1,
                        VIOCmd_prompt_1,
                        VIOServerPort_2,
                        VIOCmd_prompt_2,
                        NIM_port,
                        NIM_prompt):
        
        try:
    
            t=EThread(AIX.CreateWholeAIXVIOClient,(HMC_IP,HMCServerName,VIOClientName,min_mem,desired_mem,max_mem,min_procs,desired_procs,max_procs,min_proc_units,desired_proc_units,max_proc_units,virtual_eth_adapters,virtual_scsi_adapter,VIOServerIP_1,VIOServerUsername_1,VIOServerPasswd_1,VIOServerIP_2,VIOServerUsername_2,VIOServerPasswd_2,rootvg_lun,vhost_name,VTD_name,NIM_IP,NIM_username,NIM_passwd,ClientMgrIP,ServerHostName,spot,lpp_source,mksysb,HMC_username,HMC_passwd,VIOClientMgrGateway,VIOClientServiceIP,VIOClientServiceGateway,TargetServerUsername,TargetServerPasswd,TargetServerPort,TargetServerCmdPrompt,HMC_ssh_port,HMC_cmd_prompt,VIOServerPort_1,VIOCmd_prompt_1,VIOServerPort_2,VIOCmd_prompt_2,NIM_port,NIM_prompt))
        
        except Exception,e:
            myloger.debug('Error in AIX CreateWholeAIXVI')
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid


    #删除AIX分区完整过程
    @webservice(_params=[str,str,str,str,str,int,str,str,str,str,str,int,str,str,str,str,str,int,str,str,str,str,int,str],_returns=str)
    def RemoveWholeAIX(self,
                    HMC_IP,
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
             
        t=EThread(AIX.RemoveWholeAIXVIOClient,(HMC_IP, HMC_user, HMC_passwd, HMCServerName, VIOClientName, HMC_ssh_port, HMC_cmd_prompt, NIM_IP, NIM_username, NIM_passwd, ServerHostName, NIM_port, NIM_prompt, VIOServerIP_1, VIOServerUsername_1, VIOServerPasswd_1, VTD_name, VIOServerPort_1, VIOCmd_prompt_1, VIOServerIP_2, VIOServerUsername_2, VIOServerPasswd_2, VIOServerPort_2, VIOCmd_prompt_2))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    @webservice(_params=[str,str,str,str,str,str,int,str],_returns=str)    
    def StartVIOClient(self,
                        HMC_IP,
                        HMC_username,
                        HMC_passwd,
                        HMCServerName,
                        VIOClientName,
                        profile_name,
                        HMC_ssh_port,
                        HMC_cmd_prompt):
             
        t=EThread(HMC.StartVIOClient,(HMC_IP,HMC_username,HMC_passwd,HMCServerName,VIOClientName,profile_name,HMC_ssh_port,HMC_cmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    #shutdown vioclient from HMC
    @webservice(_params=[str,str,str,str,str,int,str],_returns=str)
    def ShutdownVIOClient(self,
                            HMC_IP,
                            HMC_username,
                            HMC_passwd,
                            HMCServerName,
                            VIOClientName,
                            HMC_ssh_port,
                            HMC_cmd_prompt):
        t=EThread(HMC.ShutdownVIOClient,(HMC_IP,HMC_username,HMC_passwd,HMCServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    #restart vioclient from HMC
    @webservice(_params=[str,str,str,str,str,int,str],_returns=str)
    def RestartVIOClient(self,
                         HMC_IP,
                      HMC_username,
                      HMC_passwd,
                      HMCServerName,
                      VIOClientName,
                      HMC_ssh_port=22,
                      HMC_cmd_prompt='#'):
        t=EThread(HMC.RestartVIOClient,(HMC_IP,HMC_username,HMC_passwd,HMCServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    #remove vioclient from HMC
    @webservice(_params=[str,str,str,str,str,int,str],_returns=str)
    def RemoveVIOClient(self,
                        HMC_IP,
                        HMC_username,
                        HMC_passwd,
                        HMCServerName,
                        VIOClientName,
                        HMC_ssh_port=22,
                        HMC_cmd_prompt='#'):
        
        t=EThread(HMC.RemoveVIOClient,(HMC_IP,HMC_username,HMC_passwd,HMCServerName,VIOClientName,HMC_ssh_port,HMC_cmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
                               
    #check aix status
    @webservice(_params=[str,str,str,str,int,str],_returns=str)
    def check_aix_status(self,
                        server_ip,
                        username,
                        passwd,
                        protocal,
                        port,
                        cmd_prompt):
        # power on: return 0,True
        # power off: return 0,False
        
        t=EThread(AIX_Check.check_aix_status,(server_ip, username, passwd, protocal, port, cmd_prompt))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid

    #get aix vioclient status
    @webservice(_params=[str,str,str,str],_returns=str)
    def get_vioclient_status(self,hmc_ip,hmc_username,hmc_passwd,server_name):
        t=EThread(HMCMonitor.GetLPARStatus,(hmc_ip,hmc_username,hmc_passwd,server_name))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    #get all servers aix vioclient status
    @webservice(_params=[str,str,str,str],_returns=str)
    def get_all_server_vioclient_status(self,hmc_ip,hmc_username,hmc_passwd,server_names_str):
        t=EThread(HMCMonitor.GetAllLparStatus,(hmc_ip,hmc_username,hmc_passwd,server_names_str))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid
    
    @webservice(_params=[str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str],_returns=str)
    def Relocate_VIOClient(self,
                      original_server_status,
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
        t=EThread(AIX.Relocate_vioclient,(original_server_status, VIOServerIP_1, VIOServerUsername_1, VIOServerPasswd_1, VIOServerPort_1, VIOCmd_prompt_1, VIOServerIP_2, VIOServerUsername_2, VIOServerPasswd_2, VIOServerPort_2, VIOCmd_prompt_2, VTD_name, rootvg_lun, vhost_name, HMC_IP, HMC_user, HMC_passwd, original_ServerName, target_ServerName, VIOClientName, profile_name, min_mem, desired_mem, max_mem, min_procs, desired_procs, max_procs, min_proc_units, desired_proc_units, max_proc_units, virtual_eth_adapters, virtual_scsi_adapter, vioclient_mgr_ip, vioclient_username, vioclient_passwd, HMC_ssh_port, HMC_cmd_prompt, Target_server_VIOServerIP_1, Target_server_VIOServerUsername_1, Target_server_VIOServerPasswd_1, Target_server_VIOServerPort_1, Target_server_VIOCmd_prompt_1, Target_server_VIOServerIP_2, Target_server_VIOServerUsername_2, Target_server_VIOServerPasswd_2, Target_server_VIOServerPort_2, Target_server_VIOCmd_prompt_2))
        tid=t.GetThreadID()
        self.ServiceThread[tid]=t
        self.ServiceThread[tid].start()
        return tid