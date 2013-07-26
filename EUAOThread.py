import threading
from time import ctime,clock
import random

class EUAOThread(threading.Thread):
    def __init__(self,func,args,name=''):
        threading.Thread.__init__(self) 
        self.name = name 
        self.func = func 
        self.args = args
        self.id=str(clock())+str(random.randint(1,100000000000))
    
    def GetTheadID(self):
        """time.clock() and random to make it unique"""
        return self.id
    
    def GetResult(self): 
        return self.res 

    def run(self): 
        print 'starting', self.name, 'at:', ctime() 
        self.res = apply(self.func, self.args) 
        print self.name, 'finished at:', ctime()
        return self.res
