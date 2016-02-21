import httplib2
import urlparse
import json
import socket
import os
import sys
import time


class elmError(Exception):
    def __init__(self, value, critical=False):
        self.value = value
        self.critical = critical

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.value



class elmServer(object):
    def __init__(self, server = '', port = ''):
        self.server     = server
        self.baseuri    = 'http://%s:%s' % (self.server, port)
        self.baseapi    = '/elemento/api'


    def get(self, url):
        method  = 'GET'
        body    = ''

        if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
    	    raise elmError('get(): url can not be None')

        h = httplib2.Http()

        try:
            response, content = h.request(uri.geturl(), method, body)
        except socket.error as err:
            raise ElementoError(err)

        if response['status'] == '200':
            return content
        elif response['status'] == '404':
	    return None
            #error = fromstring(content).find('error').text
            #raise ElementalError(error)


    def post(self, url, body):
        method = 'POST'
        header = { 'Content-type': 'application/json' }

        h = httplib2.Http()

	if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
    	    raise elmError('post(): url can not be None')

        try:
            response, content = h.request(uri.geturl(),method,json.dumps(body),header)
        except socket.error as err:
            raise elmError(err)

        if response['status'] == '201':
            return content
        #elif response['status'] == '422':
        #    error = fromstring(content).find('error').text
        #    raise ElementalError(error)
        #elif response['status'] == '404':
        #    error = fromstring(content).find('error').text
        #    raise ElementalError(error)

        #return ret


class elmJob(object):
    def __init__(self, jobId = None, server):
	self.id      = jobId
	self.server  = server

	if self.jobId is not None:
	    self.__load()

    def __load(self):
	data = self.server.get('/job/%s' % str(self.id))
	jsonData = json.loads(data)
	self.status 		= jsonData['job']['status']
	self.input_filename 	= jsonData['job']['input_filename']
	self.input_path 	= jsonData['job']['input_path']
	self.name 		= jsonData['job']['name']
	self.basename 		= jsonData['job']['basename']
	self.hls_preset_id 	= jsonData['job']['hls_preset_id']	
	self.priority 		= jsonData['job']['priority']
	self.output_path 	= jsonData['job']['output_path']
	self.system_path 	= jsonData['job']['system_path']
	self.progress 		= jsonData['job']['progress']
	self.message 		= jsonData['job']['message']
	self.worker_pid		= jsonData['job']['worker_pid']


    def start(self):
	if self.jobId is None:

elm = elmServer('54.173.2.137','8000')
x = elm.get('/job/2')

jx = elmJob(2,elm)
print jx.hls_preset_id




