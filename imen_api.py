import httplib2
import urlparse
import json
import socket


class imenError(Exception):
    def __init__(self, value, critical=False):
        self.value = value
        self.critical = critical

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.value


class imenServer(object):
    def __init__(self, server='', port=''):
        self.server = server
        self.baseuri = 'http://%s:%s' % (self.server, port)
        self.baseapi = '/imen/api'


    def get(self, url):
        method = 'GET'
        body = ''

        if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
            raise imenError('get(): url can not be None')

        h = httplib2.Http()

        try:
            response, content = h.request(uri.geturl(), method, body)
        except socket.error as err:
            raise imenError(err)

        if response['status'] == '200':
            return content
        elif response['status'] == '404':
            return None


    def post(self, url, body):
        method = 'POST'
        header = {'Content-type': 'application/json'}

        h = httplib2.Http()

        if url is not None:
            uri = urlparse.urlparse(self.baseuri + self.baseapi + url)
        else:
            raise imenError('post(): url can not be None')

        try:
            response, content = h.request(uri.geturl(), method, json.dumps(body), header)
        except socket.error as err:
            raise imenError(err)

        if response['status'] == '201':
            return content

        if response['status'] == '404':
            jsonData = json.loads(content)
            raise imenError(jsonData['message'])


class imenJob(object):
    def __init__(self, server, jobId = None):
        self.id      = jobId
        self.server  = server

        if self.id is not None:
            self.__load()
        else:
            self.thumb_preset   = None
            self.input_filename = None
            self.input_path 	= None
            self.basename       = None
            self.output_path    = None
            self.priority       = 9
            self.__status       = None
            self.__progress     = None
            self.__message      = None

    def __load(self):
        data = self.server.get('/job/%s' % str(self.id))
        jsonData = json.loads(data)
        self.thumb_preset = jsonData['job']['thumb_preset']
        self.input_filename = jsonData['job']['input_filename']
        self.input_path = jsonData['job']['input_path']
        self.basename = jsonData['job']['basename']
        self.output_path = jsonData['job']['output_path']
        self.priority = jsonData['job']['priority']
        self.__status = jsonData['job']['status']
        self.__progress = jsonData['job']['progress']
        self.__message = jsonData['job']['message']

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
                raise imenError('Server can not be None')
            if self.input_filename is None:
                raise imenError('input_filename can not be None')
            if self.input_path is None:
                raise imenError('input_path can not be None')
            if self.basename is None:
                raise imenError('basename not be None')
            if self.output_path is None:
                raise imenError('output_path can not be None')
            if self.thumb_preset is None:
                raise imenError('thumb preset can not be None')
            job = {'job':
                {
                    'thumb_preset': self.thumb_preset,
                    'input_filename': self.input_filename,
                    'input_path': self.input_path,
                    'basename': self.basename,
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
            raise imenError('Job have an id: %s. Imposible start a Job with ID' % str(self.id))