#-*- coding: utf-8 -*-
from optparse import OptionParser
import sys
import os
root_dir=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_dir)
import CommonDefinition
import subprocess, os, time, signal
import telnetlib
import paramiko
from os import linesep
import re
from time import sleep
import datetime

import platform
import commands

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)

import EUAOSSHClient

import traceback
import sys
def trace_back():
    try:
        return traceback.format_exc()
    except:
        return 'trace back error.'

def Add(a,b,c):
    """just for test multithread
    return a+b
    sleep c
    """
    sleep(c)
    return a+b

def ExecuteCMDviaTelnet(host,user,passwd,command,port=23,**kwargs):
    """
    Run command via telnet, return command status and command output
        Required:
            host: target server hostname
            user: target server username
            passwd: target server password
            command: command that need to execute
        Optional:
            port: target server telnet port
            connect_timeout: second
            command_timeout: second
            login_prompt: the word before typing username
            passwd_prompt: the word before typing passwd
            cmd_prompt: the char/word before typing command
        
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if CommonDefinition.simulation:
        # 2013.1.9 vioserver2 down, skip this server
        #if CommonDefinition.simulation or host=='182.247.251.219':
        myloger.info('simulation: telnet to %s to exec cmd: %s' % (host,command))
        exit_code=0
        output='ok'
        sleep(CommonDefinition.simulation_sleep_sec)
        return exit_code,output
    
    #initiate the args
    login_prompt=kwargs.get('login_prompt','login:')
    passwd_prompt=kwargs.get('passwd_prompt','assword:')
    cmd_prompt=kwargs.get('cmd_prompt','#')
    connect_timeout=kwargs.get('connect_timeout',60)
    command_timeout=kwargs.get('command_timeout',60)
    log=kwargs.get('log',True)
    get_exit_code=kwargs.get('get_exit_code',True)
    if log:
        myloger.debug(linesep
                  +"IP:"+host+" User:"+user+" Password:"+passwd+" Port:"+str(port)+" Connection timeout:"+str(connect_timeout)
                  +linesep
                  +"login prompt:"+login_prompt+" password prompt:"+passwd_prompt+" Command:"+command
                  +linesep)
    try:
        tn=telnetlib.Telnet(host,port,connect_timeout)
    except EOFError,e:
        if log:
            myloger.error("Telnet cannot open "+host+":"+str(port))
        commandExitCode=3
        commandOutput='Error'
        #tn.close()
        return commandExitCode,commandOutput
    except Exception,e:
        if log:
            myloger.error("Telnet cannot open %s : %s, %s" % (host,str(type(e)),+e.args[0]))
        commandExitCode=3
        commandOutput='Error'
        #tn.close()
        return commandExitCode,commandOutput
    else:
        if log:
            myloger.debug('HOST: %s connected, need to login in.' % host)
        try:
            #tn.read_until(login_prompt,connect_timeout)
            index,match,data=tn.expect([GetLastPrompt(login_prompt)],connect_timeout)
            if index!=0:
                if log:
                    myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (login_prompt,connect_timeout,data))
                commandExitCode=3
                commandOutput="Error"
                tn.close()
                return commandExitCode,commandOutput
            myloger.debug('User: %s' % user)
            tn.write(user+'\r\n')
            index,match,data=tn.expect([GetLastPrompt(passwd_prompt)],connect_timeout)
            if index==-1:
                if log:
                    myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (passwd_prompt,connect_timeout,data))
                commandExitCode=3
                commandOutput="Error"
                tn.close()
                return commandExitCode,commandOutput
            #tn.read_until(passwd_prompt,connect_timeout)
            if log:
                myloger.debug('%s OK, need password.' % user)
            tn.write(passwd+'\r\n')
            if log:
                myloger.debug('password sent.')
            index,match,data=tn.expect([GetRegObjLastPrompt(cmd_prompt)],connect_timeout)
            if index==-1:
                if log:
                    myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (cmd_prompt,connect_timeout,data))
                commandExitCode=3
                commandOutput="Error"
                tn.close()
                return commandExitCode,commandOutput
            if log:
                myloger.debug('Password OK, ready to execute command')
            
            tn.write(command+'\r\n')
            if log:
                myloger.debug('Command: [%s] sent.' % command)
            index,match,data=tn.expect([GetRegObjLastPrompt(cmd_prompt)],command_timeout)
            if index==-1:
                if log:
                    myloger.error('can not wait for %s in %d seconds, the output until now is: [%s]' % (cmd_prompt,connect_timeout,data))
                commandExitCode=3
                commandOutput="Error"
                tn.close()
                return commandExitCode,commandOutput
            #commandOutput=data.split('\r\n')[1]
            commandOutput=GetCommandOutput(data)
            
            if get_exit_code:
                #get command exit code
                tn.write("echo $?\r\n")
                #commandExitCode=tn.read_until(cmd_prompt,command_timeout)
                index,match,data=tn.expect([GetRegObjLastPrompt(cmd_prompt)],command_timeout)
                if index==-1:
                    if log:
                        myloger.error("Error in getting command: %s exit code. Return data: %s." % (command,data))
                    commandExitCode=3
                else:
                    commandExitCode=int(data.split('\r\n')[1])
                    if log:
                        myloger.debug("ExitCode: %s. Command output: %s." % (commandExitCode,commandOutput))
            else:
                commandExitCode=0
                
        except EOFError,e:
            if log:
                myloger.error("Can't read data")
            commandExitCode=3
            commandOutput='Error'
        except Exception,e:
            commandExitCode=3
            commandOutput='Error'
            if log:
                myloger.error("Error: "+str(type(e))+","+e.args[0])
        tn.close()
        return commandExitCode,commandOutput
    
def ExecuteSimpleCMDviaSSH2(host,user,passwd,command,port=22,connect_timeout=60,command_timeout=60,return_list=False):
    """
    For Simple command with single line ouput.
    Run command via SSH2, return command status and command output
        Required:
            host: target server hostname
            user: target server username
            passwd: target server password
            command: command that need to execute
        Optional:
            connect_timeout:
            port: target server telnet port
            command_timeout: second
        
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if CommonDefinition.simulation:
        myloger.info('ssh to %s to exec cmd: %s' % (host,command))
        exitCode=0
        if not return_list:
            cmdOutput='ok'
        else:
            cmdOutput=['ok']
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    myloger.debug("IP: %s, user: %s, password: %s, command: %s, connect_timeout: %d." % (host,user,passwd,command,connect_timeout))
    try:
        #ssh_client=paramiko.SSHClient()
        ssh_client=EUAOSSHClient.EUAOSSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host,port=port,username=user,password=passwd,timeout=connect_timeout)
        #ssh_client.exec_command(command,timeout=20.0)
        i,o,e=ssh_client.exec_command(command,timeout=command_timeout)
        
        if i and o and e:
            error_readlines=e.readlines()
            if error_readlines==[]:
#                commandOutput=''.join(o.readlines()).lstrip().replace('\n','')
                output_readlines=o.readlines()
                if output_readlines==[]:
                    commandOutput=''
                else:
                    output_readlines=remove_output_list_return(output_readlines)
                    if not return_list:
                        
                        commandOutput=GetSimpleSSHCommandOutput(output_readlines)
                    else:
                        commandOutput=output_readlines
                myloger.debug('Command executed successfully. Response is: %s' % commandOutput)
                commandExitCode=0
            else:
                myloger.debug('Error in executing command %s: %s.' % (command,error_readlines))
                commandOutput=error_readlines
                commandExitCode=3
        else:
            myloger.debug('Error in connection while executing command: %s.' % command)
            if not return_list:
                commandOutput=''
            else: commandOutput=[]
            commandExitCode=3
        return commandExitCode,commandOutput
    except Exception,e:
        myloger.error("SSH Adapter cannot connect to "+host+" : "+str(type(e)))
        myloger.debug(trace_back())
        commandExitCode=3
        if not return_list:
            commandOutput='Error'
        else:
            commandOutput=['Error']
        ssh_client.close()
        return commandExitCode,commandOutput
    
def ExecuteCMDviaSSH2(host,user,passwd,command,port=22,**kwargs):
    """
    Run command via SSH2, return command status and command output
        Required:
            host: target server hostname
            user: target server username
            passwd: target server password
            command: command that need to execute
        Optional:
            port: target server telnet port
            connect_timeout: second
            command_timeout: second
            cmd_prompt: the char/word before typing command
        
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if CommonDefinition.simulation:
        myloger.info('ssh to %s to exec cmd: %s' % (host,command))
        exitCode=0
        cmdOutput='ok'
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    #initiate the args
#    login_prompt=kwargs.get('login_prompt','login:')
#    passwd_prompt=kwargs.get('passwd_prompt','assword:')
    cmd_prompt=kwargs.get('cmd_prompt','#')
    connect_timeout=kwargs.get('connect_timeout',60)
    command_timeout=kwargs.get('command_timeout',60)
    myloger.debug(linesep
                  +"IP:"+host+" User:"+user+" Password:"+passwd+" Port:"+str(port)+" Connection timeout:"+str(connect_timeout)
                  +linesep
                  +" Command:"+command
                  +linesep)
    try:
        ssh_client=paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host,port=port,username=user,password=passwd,timeout=connect_timeout)
        
    except Exception,e:
        myloger.error("SSH Adapter cannot connect to "+host+" : "+str(type(e))+","+e.args[0])
        commandExitCode=3
        commandOutput='Error'
        ssh_client.close()
        return commandExitCode,commandOutput
    else:
        myloger.debug('HOST: %s connected, User %s login' % (host,user))
        try:
            ssh_channel=ssh_client.get_transport().open_session()
            ssh_channel.setblocking(0)
            ssh_channel.get_pty()
            ssh_channel.invoke_shell()
            ssh_channel.settimeout(command_timeout)
            
            #read the login info before send command
            login_info=""
            starttime=datetime.datetime.now()
            while ssh_channel.recv_ready() or login_info=="":
                tmpRecv=ssh_channel.recv(-1)
                if tmpRecv!='':
                    login_info+=tmpRecv
                    #print "login_info: %s" % login_info
                if GetRegObjLastPrompt(cmd_prompt).match(login_info.splitlines()[-1]):
                    break
                time_delta=datetime.datetime.now()-starttime
                if time_delta.total_seconds()>connect_timeout:
                    ssh_client.close()
                    ssh_channel.close()
                    myloger.error('Connection timeout.')
                    commandExitCode=1
                    commandOutput='Error'
                    return commandExitCode,commandOutput
                sleep(0.1)
            login_info=ReplaceTermControlChar(login_info)
            myloger.debug("Login Info: %s" % login_info)
            if ssh_channel.send_ready():
                # ready to send command
                ssh_channel.send(command+'\r')
                myloger.debug("Send command %s." % command) 
                command_response=""
                starttime=datetime.datetime.now()
                
                while not ssh_channel.closed and ssh_channel.recv_ready():
                    tmpRecv=ssh_channel.recv(-1)
                    if tmpRecv!='':
                        command_response+=tmpRecv
                        if GetRegObjLastPrompt(cmd_prompt).match(command_response.splitlines()[-1]):
                            break
                    time_delta=datetime.datetime.now()-starttime
                    if time_delta.total_seconds()>command_timeout:
                        myloger.error('Command timeout. Maybe the connection error or the command_timeout is not long enough for this command to be executed.')
                        ssh_client.close()
                        ssh_channel.close()
                        commandExitCode=3
                        commandOutput='Error'
                        return commandExitCode,commandOutput
                    sleep(0.1)
                        
                #get command exit code
                ssh_channel.send('echo $?\r')
                command_exit_code=""
                starttime=datetime.datetime.now()
                while not ssh_channel.closed and ssh_channel.recv_ready():
                    tmpRecv=ssh_channel.recv(-1)
                    if tmpRecv!='':
                        command_exit_code+=tmpRecv
                        if GetRegObjLastPrompt(cmd_prompt).match(command_exit_code.splitlines()[-1]):
                            break
                    time_delta=datetime.datetime.now()-starttime
                    if time_delta.total_seconds()>command_timeout:
                        myloger.error('Command timeout. Maybe the connection error.')
                        ssh_client.close()
                        ssh_channel.close()
                        commandExitCode=3
                        commandOutput='Error'
                        return commandExitCode,commandOutput
                    sleep(0.1)
                
                commandOutput=ReplaceTermControlChar(GetCommandOutput(command_response))
                commandExitCode=int(command_exit_code.splitlines()[1])
                myloger.debug("Command exit code: %s." % commandExitCode)
                myloger.debug("Command response: %s." % commandOutput)
                ssh_channel.close()
                ssh_client.close()
                return commandExitCode,commandOutput
                
                
            else:
                myloger.error('SSH Transport Channel is not ready to send command.')
                ssh_client.close()
                ssh_channel.close()
                commandExitCode=3
                commandOutput='Error'
                return commandExitCode,commandOutput
        except Exception,e:
            myloger.error("SSH Adapter error in executing command: %s." % command)
            myloger.error("Error Message: "+str(type(e))+","+e.args[0])
            ssh_client.close()
            ssh_channel.close()
            commandExitCode=3
            commandOutput='Error'
            return commandExitCode,commandOutput
        
def ExecuteMultiCMDsviaSSH2(host,user,passwd,commands,port=22,**kwargs):
    """
    Run command via SSH2, return command status and command output
        Required:
            host: target server hostname
            user: target server username
            passwd: target server password
            commands: commands,prompts,timeout that need to execute
        Optional:
            port: target server telnet port
            connect_timeout: second
            command_timeout: second
            cmd_prompt: the char/word before typing command
        
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    
    if CommonDefinition.simulation:
        myloger.info('ssh to %s to exec cmd: %s' % (host,commands))
        exitCode=0
        cmdOutput='ok'
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    #initiate the args
#    login_prompt=kwargs.get('login_prompt','login:')
#    passwd_prompt=kwargs.get('passwd_prompt','assword:')
    cmd_prompt=kwargs.get('cmd_prompt','#')
    connect_timeout=kwargs.get('connect_timeout',60)
    command_timeout=kwargs.get('command_timeout',60)
    CommandOutputlist=[]
    CommandExitCodelist=[]
    
    myloger.debug("IP: %s, User: %s, Passsword: %s, Port: %d, Connection timeout: %d, Commands: %s" % (host,user,passwd,port,connect_timeout,commands))
    try:
        ssh_client=paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host,port=port,username=user,password=passwd,timeout=connect_timeout)
        
    except Exception,e:
        myloger.error("SSH Adapter cannot connect to "+host+" : "+str(type(e))+","+e.args[0])
        commandExitCode=3
        commandOutput='Error'
        ssh_client.close()
        return commandExitCode,commandOutput
    else:
        myloger.debug('HOST: %s connected, User %s login' % (host,user))
        try:
            ssh_channel=ssh_client.get_transport().open_session()
            ssh_channel.setblocking(0)
            ssh_channel.get_pty()
            ssh_channel.invoke_shell()
            ssh_channel.settimeout(command_timeout)
            
            #read the login info before send command
            login_info=""
            starttime=datetime.datetime.now()
            while ssh_channel.recv_ready() or login_info=="":
                tmpRecv=ssh_channel.recv(-1)
                if tmpRecv!='':
                    login_info+=tmpRecv
                    print "login_info: %s" % login_info
                if GetRegObjLastPrompt(cmd_prompt).match(login_info.splitlines()[-1]):
                    break
                time_delta=datetime.datetime.now()-starttime
                if time_delta.total_seconds()>connect_timeout:
                    ssh_client.close()
                    ssh_channel.close()
                    myloger.error('Connection timeout.')
                    commandExitCode=1
                    commandOutput='Error'
                    return commandExitCode,commandOutput
                sleep(0.1)
            login_info=ReplaceTermControlChar(login_info)
            myloger.debug("Login Info: %s" % login_info)
            if ssh_channel.send_ready():
                for command in commands:
                    # ready to send command
                    if not ssh_channel.closed:
                        myloger.debug('Command, prompt and timeout: %s' % command)
                        subcommand_count=len(command)
                        if subcommand_count%3!=0:
                            myloger.error('Commands Error, command, prompt and command timeout do not appears together')
                            #ErrorExit
                            CommandExitCodelist.append(3)
                            CommandOutputlist.append(['Error'])
                            ssh_channel.close()
                            ssh_client.close()
                            return CommandExitCodelist,CommandOutputlist
                        cmd_output=[]
                        for i in range(0,subcommand_count,3):
                            cmd=command[i]
                            prt=command[i+1]
                            cmd_time_out=command[i+2]
                                
                            ssh_channel.send(cmd+'\r')
                            myloger.debug("Send command %s." % cmd) 
                            command_response=""
                            starttime=datetime.datetime.now()
                            
                            while not ssh_channel.closed and ssh_channel.recv_ready():
                                tmpRecv=ssh_channel.recv(-1)
                                if tmpRecv!='':
                                    command_response+=tmpRecv
                                    if GetRegObjLastPrompt(prt).match(command_response.splitlines()[-1]):
                                        break
                                time_delta=datetime.datetime.now()-starttime
                                if time_delta.total_seconds()>cmd_time_out:
                                    #command time out
                                    myloger.error('Command timeout. Maybe the connection error or the command time out is too short to wait for the command response.')
                                    CommandExitCodelist.append(3)
                                    CommandOutputlist.append(['Error'])
                                    ssh_channel.close()
                                    ssh_client.close()
                                    return CommandExitCodelist,CommandOutputlist
                                sleep(0.1)
                                                
                            #get command exit code
                            ssh_channel.send('echo $?\r')
                            command_exit_code=""
                            starttime=datetime.datetime.now()
                            while not ssh_channel.closed and ssh_channel.recv_ready():
                                tmpRecv=ssh_channel.recv(-1)
                                if tmpRecv!='':
                                    command_exit_code+=tmpRecv
                                    if GetRegObjLastPrompt(prt).match(command_exit_code.splitlines()[-1]):
                                        break
                                time_delta=datetime.datetime.now()-starttime
                                if time_delta.total_seconds()>cmd_time_out:
                                    #command time out
                                    myloger.error('Command timeout. Maybe the connection error.')
                                    CommandExitCodelist.append(3)
                                    CommandOutputlist.append(['Error'])
                                    ssh_channel.close()
                                    ssh_client.close()
                                    return CommandExitCodelist,CommandOutputlist
                                sleep(0.1)
                            
                            commandOutput=ReplaceTermControlChar(GetCommandOutput(command_response))
                            commandExitCode=int(command_exit_code.splitlines()[1])
                            CommandOutputlist.append(commandOutput)
                            CommandExitCodelist.append(commandExitCode)
                            myloger.debug("Command exit code: %s." % commandExitCode)
                            myloger.debug("Command response: %s." % commandOutput)
                    else:
                        myloger.error('SSH Channel closed by foreign reason')
                        return CommandExitCodelist,CommandOutputlist
                ssh_channel.close()
                ssh_client.close()
                return CommandExitCodelist,CommandOutputlist
                
            else:
                myloger.error('SSH Transport Channel is not ready to send command.')
                ssh_client.close()
                #ErrorExit
                CommandExitCodelist.append(3)
                CommandOutputlist.append(['Error'])
                ssh_channel.close()
                ssh_client.close()
                return CommandExitCodelist,CommandOutputlist
        except Exception,e:
            myloger.error("SSH Adapter error in executing command: %s." % command)
            myloger.error("Error Message: "+str(type(e))+","+e.args[0])
            #ErrorExit
            CommandExitCodelist.append(3)
            CommandOutputlist.append(['Error'])
            ssh_channel.close()
            ssh_client.close()
            return CommandExitCodelist,CommandOutputlist
        
def ExecuteMultiCMDsviaTelnet(host,user,passwd,commands,port=23,**kwargs):
    """
    Run command via telnet, return command status and command output
        Required:
            host: target server hostname
            user: target server username
            passwd: target server password
            commands: commands and prompts pair,
            
            #subcommand format:[[command,prompt,timeout],[str,str,int]]
                #example: [['ls','$',5],['pwd','$',5],['passwd','password:',5,'123','password:',5,'123','$',5]]
                       each item in commands is a list, each list contains pairs of command or subcommand and their prompts and timeout
                       after command/subcommand was successfully executed.
        Optional:
            port: target server telnet port
            connect_timeout: second
            command_timeout: second
            login_prompt: the word before typing username
            passwd_prompt: the word before typing passwd
            cmd_prompt: the char/word before typing command
        
        return:
            exitCode:
                0: success
                1: connection error
                2: command error
            commandOutput: output
    """
    if CommonDefinition.simulation:
        myloger.info('telnet to %s to exec cmd: %s' % (host,commands))
        exitCode=[0,0,0]
        cmdOutput=[['cmd 1 ok\r\n$ '], ['cmd 2 ok\r\n$ '], ['cmd 3 ok\r\n$ ']]
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    #initiate the args
    login_prompt=kwargs.get('login_prompt','login:')
    passwd_prompt=kwargs.get('passwd_prompt','assword:')
    cmd_prompt=kwargs.get('cmd_prompt','#')
    connect_timeout=kwargs.get('connect_timeout',60)
    command_timeout=kwargs.get('command_timeout',60)
    CommandOutputlist=[]
    CommandExitCodelist=[]
    myloger.debug("IP: %s, User: %s, Passsword: %s, Port: %d, Connection timeout: %d, login prompt: %s, password prompt: %s, Commands: %s" % (host,user,passwd,port,connect_timeout,login_prompt,passwd_prompt,commands))
    try:
        tn=telnetlib.Telnet(host,port,connect_timeout)
    except EOFError,e:
        myloger.error("Telnet cannot open "+host+":"+str(port))
        CommandExitCodelist.append(3)
        CommandOutputlist.append(['Error'])
        tn.close()
        return CommandExitCodelist,CommandOutputlist
    except Exception,e:
        myloger.error("Telnet cannot open "+host+" : "+str(type(e))+","+e.args[0])
        CommandExitCodelist.append(3)
        CommandOutputlist.append(['Error'])
        tn.close()
        return CommandExitCodelist,CommandOutputlist
    else:
        myloger.debug('HOST: %s connected, need to login in.' % host)
        try:
            #tn.read_until(login_prompt,connect_timeout)
            index,match,data=tn.expect([GetLastPrompt(login_prompt)],connect_timeout)
            if index!=0:
                myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (login_prompt,connect_timeout,data))
                CommandExitCodelist.append(3)
                CommandOutputlist.append(['Error'])
                tn.close()
                return CommandExitCodelist,CommandOutputlist
            myloger.debug('User: %s' % user)
            tn.write(user+'\r\n')
            index,match,data=tn.expect([GetLastPrompt(passwd_prompt)],connect_timeout)
            if index==-1:
                myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (passwd_prompt,connect_timeout,data))
                CommandExitCodelist.append(3)
                CommandOutputlist.append(["Error"])
                tn.close()
                return CommandExitCodelist,CommandOutputlist
            #tn.read_until(passwd_prompt,connect_timeout)
            myloger.debug('%s OK, need password.' % user)
            tn.write(passwd+'\r\n')
            myloger.debug('password sent.')
            index,match,data=tn.expect([GetRegObjLastPrompt(cmd_prompt)],connect_timeout)
            if index==-1:
                myloger.error("can not wait for %s in %d seconds, the output until now is: [%s]" % (cmd_prompt,connect_timeout,data))
                CommandExitCodelist.append(3)
                CommandOutputlist.append(['Error'])
                tn.close()
                return CommandExitCodelist,CommandOutputlist
            myloger.debug('Password OK, ready to execute command')
            
            #commands
            for command in commands:
                myloger.debug('Command and prompt: %s' % command)
                #subcommand format:[[command,prompt,timeout],[str,str,int]]
                #example: [['ls','$',5],['pwd','$',5],['passwd','password:',5,'123','password:',5,'123','$',5]]
                subcommand_count=len(command)
                if subcommand_count%3!=0:
                    myloger.error('Commands Error, command, prompts and command timeout do not appear in pairs')
                    #ErrorExit
                    CommandExitCodelist.append(3)
                    CommandOutputlist.append(['Error'])
                    tn.close()
                    return CommandExitCodelist,CommandOutputlist
                
                cmd_output=[]               
                for i in range(0,subcommand_count,3):
                    cmd=command[i]
                    prt=command[i+1]
                    cmd_time_out=command[i+2]
                    tn.write(cmd+'\r\n')
                    myloger.debug('Commands: %s sent.' % cmd)
                    index,match,data=tn.expect([GetRegObjLastPrompt(prt)],cmd_time_out)
                    if index==-1:
                        myloger.error('can not wait for %s in %d seconds, the output until now is: [%s]' % (cmd_prompt,connect_timeout,data))
                        CommandExitCodelist.append(3)
                        CommandOutputlist.append(['Error'])
                        tn.close()
                        return CommandExitCodelist,CommandOutputlist
                    myloger.debug("%s output: %s" % (cmd,data))
                    cmd_output.append(data)
                CommandOutputlist.append(cmd_output)
                
                #get command exit code
                tn.write("echo $?\r\n")
                index,match,data=tn.expect([GetRegObjLastPrompt(cmd_prompt)],command_timeout)
                if index==-1:
                    ErrStr="Error in getting command: %s exit code. Return data: %s." % (command,data)
                    myloger.error(ErrStr)
                    CommandOutputlist.append([ErrStr])
                    CommandExitCodelist.append(3)
                    return CommandExitCodelist,CommandOutputlist
                else:
                    commandExitCode=int(data.split('\r\n')[1])
                    CommandExitCodelist.append(commandExitCode)
                    myloger.debug("ExitCode: %s, Command output: %s." % (commandExitCode,cmd_output))
        except EOFError,e:
            myloger.error("Can't read data")
            CommandExitCodelist.append(3)
            CommandOutputlist.append(['Error: Can not read data.'])
            
        except Exception,e:
            commandExitCode=3
            CommandOutputlist.append(['Error'])
            myloger.error("Error: "+str(type(e))+","+e.args[0])
        tn.close()
        return CommandExitCodelist,CommandOutputlist
    
def GetLastPrompt(prompt):
    """
    form a regular express string:  '.*'+prompt+'\ $'
    """
    return '.*'+prompt+'\ $'

def GetRegObjLastPrompt(prompt):
    """
    Use RegExp mutiline mode, for some first login and some command with multiline output
    """
    if prompt.find('$')>=0:
        prompt=prompt.replace('$','\$')
    return re.compile('^.*'+prompt+'\ ?$',re.MULTILINE)

def remove_output_list_return(data):
    return_list=[]
    for item in data:
        return_list.append(item.replace('\n',''))
    return return_list

def GetSimpleSSHCommandOutput(data):
    """
    here data is a list.
    
    """
    data_item_count=len(data)
    if data_item_count>1:
        str_linesep=CommonDefinition.line_sep
        data_str=''
        for i in range(data_item_count-1):
            data_str+=data[i]
            data_str+=str_linesep
        data_str+=data[data_item_count-1]
        return data_str
    elif data_item_count==1:
        return data[0]
    else:
        return ''

def GetCommandOutput(data):
    """
    remove the first and last line,return the raw output
    data: str
    return data_output
    *** Notice ***
    This function works in low efficiency, it should be replace in the future.
    """
    str_linesep='\r\n'
    data_list=str(data).split(str_linesep)
    if len(data_list)>=3:
        data_list=data_list[1:-1]
        return_str=data_list[0]
        for item in data_list[1:]:
            return_str=return_str+str_linesep
            return_str=return_str+item
        return return_str
    elif len(data_list)==2:
        return ''
    else:
        return data
    #return ''.join(str(data).split('\r\n')[1:-1])
    
def ReplaceTermControlChar(data):
    """
    remore the Terminal Control Characters
    """
    # for linux
    strinfo=re.compile('\\x1b.{1,6}?m')
    return strinfo.sub('',data)

def ExecuteSimpleCMDLocal(cmd):
    
    if CommonDefinition.simulation:
        myloger.info('local exec cmd: %s' % commands)
        exitCode=0
        cmdOutput='ok'
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    myloger.debug('Local command: %s' % cmd)
    platform_system=platform.system()
    if platform_system=='Windows':
        return os.system(cmd),''
    elif platform_system=='Linux':
        return commands.getstatusoutput(cmd)
    
def ExecuteCMDLocal(cmd,timeout=5):
    """
    timeout: seconds
    
    """
    
    if CommonDefinition.simulation:
        myloger.info('local exec cmd: %s' % commands)
        exitCode=0
        cmdOutput='ok'
        sleep(CommonDefinition.simulation_sleep_sec)
        return exitCode,cmdOutput
    
    myloger.debug('Local command: %s' % cmd)
    platform_system=platform.system()
    if platform_system=='Windows':
        myloger.debug('Execute command in local cmd: %s' % cmd)
        try:
            output=os.popen(cmd)
            CommandOutput=output.read()
            
            myloger.debug('Command Output: %s' % CommandOutput)
            o=os.popen('echo %errorlevel%')
            ExitCode=o.read()
            print ExitCode,CommandOutput
        except Exception,e:
            myloger.error('Error while executing command \'%s\' in local CMD. %s, %s' % (cmd,str(type(e)),e.args[0]))
            ExitCode=3
            return ExitCode,''
    elif platform_system=='Linux':
        cmds = cmd.split(" ")
        start = datetime.datetime.now()
        try:
            process = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while process.poll() is None:
                time.sleep(0.2)
                now = datetime.datetime.now()
                if (now - start).seconds> timeout:
                    os.kill(process.pid, signal.SIGILL)
                    """
                    waitpid(pid, options) -> (pid, status << 8)
                    Wait for completion of a given process.  options is ignored on Windows.
                    """
                    os.waitpid(-1,0)
                    ExitCode=3
                    Output='Execute command \'%s\' Timeout. Timeout is %d second' % (cmd,timeout)
                    return ExitCode,Output
            Output=process.stdout.readlines()
        except Exception,e:
            myloger.error('Error while executing command \'%s\' in local CMD. %s, %s' % (cmd,str(type(e)),e.args[0]))
            ExitCode=3
            return ExitCode,''
                
        o=os.popen('echo %errorlevel%')
        ExitCode=o.read()
        print ExitCode,Output
        return ExitCode,Output        
    else:
        errorMsg='EUAO Base Adapter ExecuteCMDLocal Function does no support Platform: %s' % platform_system
        myloger.error(errorMsg)
        ExitCode=3
        return ExitCode,errorMsg


if __name__ == '__main__':
    #ExecuteCMDviaTelnet('182.247.251.215','padmin','padmin','pwd',cmd_prompt='$')
    """
    ExecuteCMDLocal('vol',timeout=4)
    ExecuteCMDLocal('java -jar',timeout=4)
    """
    """
    username='padmin'
    passwd='padmin'
    cmd_list=[['cp .sh_history a','$',5],['cp .sh_history b','$',5],['cp .sh_history c','$',5]]
    exit_code,output=ExecuteMultiCMDsviaTelnet('182.247.251.219',username,passwd,cmd_list,port=23,cmd_prompt='$')
    print exit_code
    print output
    """
    
    exit_code,result=ExecuteSimpleCMDviaSSH2('182.247.251.247','hscroot','abc1234','pwd')
    print exit_code
    print result
