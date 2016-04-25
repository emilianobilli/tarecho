import httplib2
import urlparse
import json
import socket
import os
import sys
import time


class elmCafioloError(Exception):
    def __init__(self, value, critical=False):
        self.value = value
        self.critical = critical

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.value


class elmCafioloServer(object):
    def __init__(self, server = '', port = ''):
        self.server             = server
        self.baseuri            = 'http://%s:%s' % (self.server, port)
        self.baseapi            = '/elmcafiolo/api'

#        if self.server is not None:
#            self.__load()
#        else:
#            self.__slots	                = None


    def get(self, url):
        method  = 'GET'
        body    = ''

        if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
            raise elmCafioloError('get(): url can not be None')

        h = httplib2.Http()

        try:
            response, content = h.request(uri.geturl(), method, body)
        except socket.error as err:
            raise elmCafioloError(err)

        if response['status'] == '200':
            return content
        elif response['status'] == '404':
            return None


    def post(self, url, body):
        method = 'POST'
        header = { 'Content-type': 'application/json' }

        h = httplib2.Http()

        if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
            raise elmCafioloError('post(): url can not be None')

        try:
            response, content = h.request(uri.geturl(),method,json.dumps(body),header)
        except socket.error as err:
            raise elmCafioloError(err)
	
        if response['status'] == '201':
	    return content
	
	if response['status'] == '404':
	    jsonData = json.loads(content)
	    raise elmCafioloError(jsonData['message'])


class elmCafioloJob(object):
    def __init__(self, server, jobId = None):
        self.id      = jobId
        self.server  = server

        if self.id is not None:
            self.__load()
        else:
	    self.name 		= None
	    self.preset 	= None
	    self.input_filename = None
	    self.input_path 	= None
	    self.transcoder 	= None
	    self.basename	= None
	    self.output_path 	= None
	    self.priority 	= 9
	    self.__status 	= None
	    self.__progress 	= None
            self.__message 	= None
            

    def __load(self):
        data = self.server.get('/job/%s' % str(self.id))
        jsonData = json.loads(data)
	self.name               = jsonData['job']['name']
	self.preset      	= jsonData['job']['preset']
	self.input_filename     = jsonData['job']['input_filename']
	self.input_path         = jsonData['job']['input_path']
	self.transcoder		= jsonData['job']['transcoder']
	self.basename           = jsonData['job']['basename']
	self.output_path        = jsonData['job']['output_path']	
	self.priority           = jsonData['job']['priority']
        self.__status           = jsonData['job']['status']
        self.__progress         = jsonData['job']['progress']
        self.__message          = jsonData['job']['message']
        

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
                raise elmCafioloError('Server can not be None')
            if self.input_filename is None:
                raise elmCafioloError('input_filename can not be None')
            if self.input_path is None:
                raise elmCafioloError('input_path can not be None')
            if self.basename is None:
                raise elmCafioloError('basename not be None')
            if self.output_path is None:
                raise elmCafioloError('output_path can not be None')
            if self.name is None:
                raise elmCafioloError('name can not be None')
            if self.preset is None:
                raise elmCafioloError('preset can not be None')
            job = {'job' :
                    {
                    'name': self.name,
                    'preset': self.preset,
                    'input_filename': self.input_filename,
                    'input_path': self.input_path,
                    'basename': self.basename,
                    'output_path': self.output_path,
                    'priority': self.priority
                    }
                   }

            response = self.server.post('/job/', job)
	    print response
	    responseJson = json.loads(response)
            self.id = responseJson['job']['id']
            self.__load()
            return self.id
        else:
            raise elmCafioloError('Job have an id: %s. Imposible start a Job with ID' % str(self.id))



