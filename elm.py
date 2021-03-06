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
        self.server     	= server
        self.baseuri    	= 'http://%s:%s' % (self.server, port)
        self.baseapi    	= '/elemento/api'
    
	if self.server is not None:
	    self.__load()
	else:
	    self.__workers			= None
	    self.__temporal_path		= None
	    self.__output_basepath		= None
	    self.__delete_on_success	= None
	    self.__report_loglevel		= None
	    self.__ffmpeg_bin		= None
	    self.__advanced_options		= None

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
            raise elmError(err)

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
	
    def __load(self):
	data = self.get('/config/')
	jsonData = json.loads(data)
	self.__workers			= jsonData['config']['workers']
	self.__temporal_path		= jsonData['config']['temporal_path']
	self.__output_basepath		= jsonData['config']['output_basepath']
	self.__delete_on_success	= jsonData['config']['delete_on_success']
	self.__report_loglevel		= jsonData['config']['report_loglevel']
	self.__ffmpeg_bin		= jsonData['config']['ffmpeg_bin']
	self.__advanced_options		= jsonData['config']['advanced_options']

    def workers(self):
	if self.server is not None:
	    self.__load()
	    return self.__workers


    def preset(self, name):
	method = 'GET'
	body   = ''

	data = self.get('/preset/%s/' % name)
	if data is not None:
	    jsonData = json.loads(data)
	    id = jsonData['preset']['id']
	    type = jsonData['preset']['type']
	    return id, type
	
	return None, None

class elmJob(object):
    def __init__(self, server, jobId = None):
	self.id      = jobId
	self.server  = server

	if self.id is not None:
	    self.__load()
	else:
	    self.__status = None
	    self.input_filename = None
	    self.input_path = None
	    self.name = None
	    self.basename= None
	    self.hls_preset_id = None
	    self.h264_preset_id = None
	    self.priority = 9
	    self.output_path = None
	    self.system_path = False
	    self.__progress = None
	    self.__message = None
	    self.worker_pid = None

    def __load(self):
	data = self.server.get('/job/%s' % str(self.id))
	jsonData = json.loads(data)
	self.__status 		= jsonData['job']['status']
	self.input_filename 	= jsonData['job']['input_filename']
	self.input_path 	= jsonData['job']['input_path']
	self.name 		= jsonData['job']['name']
	self.basename 		= jsonData['job']['basename']
	self.hls_preset_id 	= jsonData['job']['hls_preset_id']	
	self.h264_preset_id	= jsonData['job']['h264_preset_id']
	self.priority 		= jsonData['job']['priority']
	self.output_path 	= jsonData['job']['output_path']
	self.system_path 	= jsonData['job']['system_path']
	self.__progress		= jsonData['job']['progress']
	self.__message 		= jsonData['job']['message']
	self.worker_pid		= jsonData['job']['worker_pid']

    

    def files(self):
	returnFiles = []
	data = self.server.get('/job/%s/outputfile/' % str(self.id))
	jsonData = json.loads(data)
	if jsonData is not {}:
	    for f in jsonData['job']['outputfile']:
		returnFiles.append(f)

	return returnFiles


    def status(self):
	if self.id is not None:
	    self.__load()
	    return self.__status

    def message(self):
	if self.id is not None:
	    self.__load()
	    return self.__message

    def progress(self):
	if self.id is not None:
	    self.__load()
	    return self.__progress

    def start(self):
	if self.id is None:
    	    if self.server is None:
		raise elmError('Server can not be None')
	    if self.input_filename is None:
		raise elmError('input_filename can not be None')
	    if self.input_path is None:
		raise elmError('input_path can not be None')
	    if self.basename is None:
		raise elmError('basename not be None')
	    if self.output_path is None:
		raise elmError('output_path can not be None')
	    if self.name is None:
		raise elmError('name can not be None')
	    if self.hls_preset_id is None and self.h264_preset_id is None:
		raise elmError('hls_preset or h264_preset can not be None')
	    if self.hls_preset_id is not None:
    		job = {'job' :
		    	{
			'name': self.name,
			'hls_preset_id': self.hls_preset_id,
			'input_filename': self.input_filename,
			'input_path': self.input_path,
			'basename': self.basename,
			'system_path': self.system_path,
			'output_path': self.output_path,
			'priority': self.priority
			}
		       }
	    else:
		job = {'job' :
		    	{
			'name': self.name,
			'h264_preset_id': self.h264_preset_id,
			'input_filename': self.input_filename,
			'input_path': self.input_path,
			'basename': self.basename,
			'system_path': self.system_path,
			'output_path': self.output_path,
			'priority': self.priority
			}
		       }

	    response = self.server.post('/job/', job)
	    responseJson = json.loads(response)
	    self.id = responseJson['job']['id']
	    self.__load()
	    return self.id
	else:
	    raise elmError('Job have an id: %s. Imposible start a Job with ID' % str(self.id))
