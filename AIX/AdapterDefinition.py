#-*- coding: utf-8 -*-

#Adapter Class Path
#BaseAdapter.py
import CommonDefinition

BaseAdapter_dir=CommonDefinition.path_dir_sep+'BaseAdapter'
#AIX
AIX=CommonDefinition.path_dir_sep+'AIX'

#HP
HPUX=CommonDefinition.path_dir_sep+'HPUX'

VMware=CommonDefinition.path_dir_sep+'VMware'

import sys
import os
root_dir=os.path.split(os.path.realpath(__file__))[0]
