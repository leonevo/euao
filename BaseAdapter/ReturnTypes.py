#!/usr/bin/env python
#-*- coding: utf-8 -*-import threading
from tornadows.complextypes import ComplexType

class TelnetReturnType(ComplexType):
    ExitCode=int
    CommandOutput=str
    
class SSHReturnType(ComplexType):
    ExiteCode=int
    CommandOutput=str

class CommandReturnType(ComplexType):
    ExitCode=int
    CommandOutput=str

class ThreadReturnType(ComplexType):
    tid=str