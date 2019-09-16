# adapted from firebase/EventSource-Examples/python/chat.py by Shariq Hashme

from usseclient import SSEClient
import urequests as requests
from urllib import urlencode, quote

import ujson as json
import _thread as thread
import usocket as socket


class ClosableSSEClient(SSEClient):
    def __init__(self, *args, **kwargs):
        self.should_connect = True
        super(ClosableSSEClient, self).__init__(*args, **kwargs)

    def _connect(self):
        if self.should_connect:
            super(ClosableSSEClient, self)._connect()
        else:
            raise StopIteration()


def close(self):
    self.should_connect = False
    self.retry = 0
    try:
        self.resp.raw._fp.fp._sock.shutdown(socket.SHUT_RDWR)
        self.resp.raw._fp.fp._sock.close()
    except AttributeError:
        pass


class RemoteThread():
    def __init__(self, parent, URL, function):
        self.function = function
        self.URL = URL
        self.parent = parent
        super(RemoteThread, self).__init__()

    def run(self):
        try:
            self.sse = ClosableSSEClient(self.URL)
            for msg in self.sse:
                msg_data = json.loads(msg.data)
                if msg_data is None:  # keep-alives
                    continue
                msg_event = msg.event
                # TODO: update parent cache here
                self.function((msg.event, msg_data))
        except socket.error:
            pass  # this can happen when we close the stream
        except KeyboardInterrupt:
            self.close()


def start(self, run):
    thread.start_new_thread(run)

    def stop(self):
        thread.exit()


def close(self):
    if self.sse:
        self.sse.close()


def firebaseURL(URL):
    if '.firebaseio.com' not in URL.lower():
        if '.json' == URL[-5:]:
            URL = URL[:-5]
        if '/' in URL:
            if '/' == URL[-1]:
                URL = URL[:-1]
            URL = 'https://' + \
                  URL.split('/')[0] + '.firebaseio.com/' + URL.split('/', 1)[1] + '.json'
        else:
            URL = 'https://' + URL + '.firebaseio.com/.json'
        return URL

    if 'http://' in URL:
        URL = URL.replace('http://', 'https://')
    if 'https://' not in URL:
        URL = 'https://' + URL
    if '.json' not in URL.lower():
        if '/' != URL[-1]:
            URL = URL + '/.json'
        else:
            URL = URL + '.json'
    return URL


class subscriber:
    def __init__(self, URL, function):
        self.cache = {}
        self.remote_thread = RemoteThread(self, firebaseURL(URL), function)

    def start(self):
        self.remote_thread.start()

    def stop(self):
        self.remote_thread.stop()


class FirebaseException(Exception):
    pass

class Database:
    def __init__(self, credentials, api_key, database_url):

        if not database_url.endswith('/'):
            url = ''.join([database_url, '/'])
        else:
            url = database_url

        self.credentials = credentials
        self.api_key = api_key
        self.database_url = url

        self.path = ""
        self.build_query = {}
        self.last_push_time = 0
        self.last_rand_chars = []

    def put(URL, msg):
        to_post = json.dumps(msg)
        response = requests.put(firebaseURL(URL), data=to_post)
        if response.status_code != 200:
            raise FirebaseException(response.text)


    def patch(URL, msg):
        to_post = json.dumps(msg)
        response = requests.patch(firebaseURL(URL), data=to_post)
        if response.status_code != 200:
            raise FirebaseException(response.text)


    def get(self, token):
        request_ref = Database.build_request_url(self, token)
        response = requests.get(request_ref)
        if response.status_code != 200:
            raise FirebaseException(response.text)
        return json.loads(response.text)

    def push(URL, msg):
        to_post = json.dumps(msg)
        response = requests.post(firebaseURL(URL), data=to_post)
        if response.status_code != 200:
            raise Exception(response.text)


    def child(self, *args):
        new_path = "/".join([str(arg) for arg in args])
        if self.path:
            self.path += "/{}".format(new_path)
        else:
            if new_path.startswith("/"):
                new_path = new_path[1:]
            self.path = new_path
        return self

    def build_request_url(self, token):
        parameters = {}
        if token:
            parameters['auth'] = token
        for param in list(self.build_query):
            if type(self.build_query[param]) is str:
                parameters[param] = quote('"' + self.build_query[param] + '"')
            elif type(self.build_query[param]) is bool:
                parameters[param] = "true" if self.build_query[param] else "false"
            else:
                parameters[param] = self.build_query[param]
        # reset path and build_query for next query
        request_ref = '{0}{1}.json?{2}'.format(self.database_url, self.path, urlencode(parameters))
        self.path = ""
        self.build_query = {}
        return request_ref


class Auth:
    def __init__(self, api_key, credentials):
        self.api_key = api_key
        self.current_user = None
        self.credentials = credentials

    def sign_in_with_email_and_password(self, email, password):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        request_object = requests.post(request_ref, headers=headers, data=data)
        self.current_user = request_object.json()
        return request_object.json()

def initialize_app(config):
    return Firebase(config)

class Firebase:
    """ Firebase Interface """
    def __init__(self, config):
        self.api_key = config["apiKey"]
        self.auth_domain = config["authDomain"]
        self.database_url = config["databaseURL"]
        self.storage_bucket = config["storageBucket"]
        self.credentials = None

    def auth(self):
        return Auth(self.api_key, self.credentials)

    def database(self):
        return Database(self.credentials, self.api_key, self.database_url)
