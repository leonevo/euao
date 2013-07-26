#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
把一些人去操作的时候不会关心的配置参数定义在这里。
而如IP、用户名、密码等属性，人工操作也需要的，则通过函数接口传入
"""
#NIM
NIM_prompt='#'
NIM_port=23

#VIO
#each VIOServer config should be the same
VIOServer_prompt='$'
VIOServer_port=23

#HMC
HMC_prompt='hscroot@localhost:~>'
HMC_port=22

#AIX Common
AIX_TelnetPort=23
AIX_Cmd_prompt='#'
AIX_Default_Username='root'
AIX_Default_Passwd='root'