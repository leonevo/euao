#!/usr/bin/env python
#
# Copyright 2011 Rodrigo Ancavil del Pino
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

""" Implementation of webservices API 0.9 """

import tornado.httpserver
import tornado.ioloop
import tornado.web

class WebService(tornado.web.Application):
	""" A implementation of web services for tornado web server.

		import tornado.httpserver
		import tornado.ioloop
		from tornadows import webservices
		from tornadows import xmltypes
	   	from tornadows import soaphandler
		from tornadows.soaphandler import webservice
 
		class MyService(soaphandler.SoapHandler):
			@webservice(_params=[xmltypes.Integer, xmltypes.Integer],_returns=xmltypes.Integer)
			def sum(self, value1, value2):
				result = value1 + value2
	
				return result  

		if __name__ == "__main__":
			app = webservices.WebService("MyService",MyService)
			ws_server = tornado.httpserver.HTTPServer(app)
			ws_server.listen(8080)
			tornado.ioloop.IOLoop.instance().start()
		
	"""
	def __init__(self,services,object=None,wsdl=None):
		""" Initializes the application for web services

		    Instances of this class are callable and can be passed to
		    HTTPServer of tornado to serve the web services.

		    The constructor for this class takes the name for the web 
		    service (service), the class with the web service (object) 
		    and wsdl with the wsdl file path (if this exist).
		 """
		if isinstance(services,list) and object == None:
			srvs = []
			for s in services:
				srv = s[0]
				obj = s[1]
				srvs.append((r"/"+str(srv),obj))
				srvs.append((r"/"+str(srv)+"/",obj))
			tornado.web.Application.__init__(self,srvs)
		else:
			self._service = services
			self._object = object
			self._services = [(r"/"+str(self._service),self._object),
					  (r"/"+str(self._service)+"/",self._object),]
			tornado.web.Application.__init__(self,self._services)

