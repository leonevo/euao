#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2012 leon.tan@ce-service.com.cn
#
import tornado.httpserver
import tornado.ioloop
from tornadows import soaphandler
from tornadows import webservices
from tornadows import xmltypes
from tornadows.soaphandler import webservice
from time import ctime,sleep

import CommonDefinition
#process web service class import
import os
import sys
cur_dir=os.path.dirname(os.path.abspath(__file__))
AIX_dir=cur_dir+CommonDefinition.path_dir_sep+'AIX'
sys.path.append(AIX_dir)

EMC_dir=cur_dir+CommonDefinition.path_dir_sep+'EMC'
sys.path.append(EMC_dir)

VMware_dir=cur_dir+CommonDefinition.path_dir_sep+'VMware'
sys.path.append(VMware_dir)

HP_dir=cur_dir+CommonDefinition.path_dir_sep+'HP'
sys.path.append(HP_dir)

from ControlAIX import ControlAIX
from ControlEMC import ControlEMC
from ControlVMware import ControlVMware
from ControlHP import ControlHP
if __name__ == '__main__':
    service=[('ControlAIX',ControlAIX),
              ('ControlEMC',ControlEMC),
              ('ControlVMware',ControlVMware),
              ('ControlHP',ControlHP)]
    app=webservices.WebService(service)
    ws=tornado.httpserver.HTTPServer(app)
    port=CommonDefinition.Tornado_port
    ws.listen(port)
    tornado.ioloop.IOLoop.instance().start()