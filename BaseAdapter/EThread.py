#!/usr/bin/env python
#-*- coding: utf-8 -*-
import threading
from time import ctime,clock
import random
import sys
import os
root_dir=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_dir)
import CommonDefinition

#log setting
import logging
myloger=logging.getLogger(CommonDefinition.loggerName)

class EThread(threading.Thread):
    def __init__(self,func,args,name='EThread'):
        threading.Thread.__init__(self) 
        self.name = name 
        self.func = func 
        self.args = args
        self.id=str(clock())+'-'+str(random.randint(1,100000000000))
    
    def GetThreadID(self):
        """time.clock() and random to make it unique"""
        return self.id
    
    def GetResult(self): 
        return self.res 

    def run(self):
        myloger.debug('starting %s-%s at %s.' % (self.name,self.id,str(ctime())))
        self.res = apply(self.func, self.args)
        myloger.debug('finished %s-%s at %s.' % (self.name,self.id,str(ctime())))
        return self.res
