#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import json
import random
import string

try:
    from sha import new as sha1
except ImportError:
    from hashlib import sha1
from six.moves.urllib import parse as urllib_parse

import requests

# By explicitly listing endpoints, we can get tab completion and help etc. when
# using Client interactively or in an IDE.
API_RESOURCES = [
    'token',

    'automation',
    'clickAutomation',
    'dateAutomation',
    'openAutomation',
    'smsAutomation',
    'subscriptionAutomation',
    'bounce',
    'contact',
    'doNotContact',
    'emailOpen',
    'emailLinkClick',
    'folder',
    'form',
    'import',
    'list',
    'message',
    'emailMessage',
    'emailMessageLink',
    'smsMessage',
    'sms',
    'smsDestination',
    'preview',
    'splitTest',
    'subscriber',
    'subscriberProfileData',
    'subscriberProfileField',
    'subscription',
    'task',
    'user',
]

SignuptoResponse = namedtuple('SignuptoResponse', 'data next count')


class ServerHttpError(ValueError):
    """
    Indicates HTTP error code.
    """
    def __init__(self, message, status_code):
        super(HttpError, self).__init__(message)
        self.status_code = status_code


class ClientError(ValueError):
    """
    Indicates error made by programmer using this library.
    Used when the server returns a JSON document indicating the error.
    """
    def __init__(self, message, error_info, status_code):
        super(ClientError, self).__init__(message)
        self.error_info = error_info
        self.status_code = status_code


class ObjectNotFound(ClientError):
    pass


class NoAuthorization(object):
    def make_authorized_request(self, handler, method, url, data=None, params=None, headers=None):
        return handler(method, url, data=data, params=params, headers=headers)


def make_hash_authorization_signature(method, url, date_string, company_id, user_id, nonce, api_key):
    s = ("%(method)s %(path)s\r\n"
         "Date: %(date_string)s\r\n"
         "X-SuT-CID: %(company_id)s\r\n"
         "X-SuT-UID: %(user_id)s\r\n"
         "X-SuT-Nonce: %(nonce)s\r\n"
         "%(api_key)s"

         % dict(method=method,
                path=urllib_parse.urlparse(url).path.rstrip('/'),
                date_string=date_string,
                company_id=company_id,
                user_id=user_id,
                nonce=nonce,
                api_key=api_key)
         )
    return sha1(s.encode('utf-8')).hexdigest()


class HashAuthorization(object):
    def __init__(self, company_id=None, user_id=None, api_key=None):
        self.company_id = company_id
        self.user_id = user_id
        self.api_key = api_key

    def make_nonce(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(40))

    def make_authorized_request(self, handler, method, url, data=None, params=None, headers=None):
        if headers is None:
            headers = {}
        nonce = self.make_nonce()
        headers['X-SuT-Nonce'] = nonce
        headers['X-SuT-CID'] = str(self.company_id)
        headers['X-SuT-UID'] = str(self.user_id)
        date_string = format_date_time(mktime(datetime.now().timetuple()))
        headers['Date'] = date_string

        signature = make_hash_authorization_signature(method, url, date_string, self.company_id, self.user_id, nonce, self.api_key)
        headers['Authorization'] = 'SuTHash signature="%s"' % signature
        return handler(method, url, data=data, params=params, headers=headers)


class TokenAuthorization(object):

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.initialized = False

    def initialize(self, version=None):
        # We have to do an unauthenticated request to initialize
        temp_client = Client(version=version,
                             auth=None)
        r = temp_client.token.post(username=self.username, password=self.password)
        self.token = r.data['token']
        self.expiry = r.data['expiry']
        self.initialized = True

    def make_authorized_request(self, handler, method, url, data=None, params=None, headers=None):
        if headers is None:
            headers = {}
        headers['Authorization'] = "SuTToken %s" % self.token
        return handler(method, url, params=params, headers=headers)


class Client(object):
    """
    Main entry point.

    Client() should be instantiated with 'auth' keyword argument,
    which should be an instance of HashAuthorization or TokenAuthorization.

    sign-up.to endpoints are available as resources on the Client instance.
    Resources have 'get', 'put', 'post', 'head' and 'delete' methods, which
    take the documented sign-up.to parameters as keyword arguments. e.g.:

    >>> c = Client(auth=HashAuthorization(...))
    >>> c.list.get(id="mylist")

    These methods return a SignuptoResponse object, which contains the
    'response' attribute of the API call, that is, an object with these
    attributes:

    - data - the data returned by the API call, converted to native Python objects
             e.g. a Python dictionary containing list information, or an array.

    - next - value representing the resource following the last returned resource.

    - count - the number of resources returned.

    https://dev.sign-up.to/documentation/reference/latest/making-requests/response-format/

    Any error (e.g. when the status is not "OK") will cause an exception to be
    raised.

    """
    extra_headers = {'Accept': 'application/json',
                     'Content-Type': 'application/json',
                     }


    def __init__(self, version="0", auth=None):
        if hasattr(auth, 'initialize') and not getattr(auth, 'initialized', False):
            auth.initialize(version=version)
        self.baseurl = 'https://api.sign-up.to/v%s/' % version
        if auth is None:
            auth = NoAuthorization()
        self.auth = auth

    def make_request_raw(self, method, url, data='', params=None, headers=None):
        return requests.request(method, url, data=data, params=params, headers=headers)

    def make_request(self, method, resource_name, data=None, params=None, headers=None):
        url = self.baseurl + resource_name
        if headers is None:
            headers = {}
        h2 = {}
        h2.update(self.extra_headers)
        h2.update(headers)
        response = self.auth.make_authorized_request(self.make_request_raw,
                                                     method,
                                                     url,
                                                     data=json.dumps(data),
                                                     params=params,
                                                     headers=h2)
        return self.handle_response(response)

    def handle_response(self, response):
        code = response.status_code
        if 500 <= code:
            raise ServerHttpError(response.content, code)
        else:
            assert code < 300 or code >= 400 # Redirections should have been handled
            return self.deserialize(response)

    def deserialize(self, response):
        error_cls = None
        if 400 <= response.status_code < 500:
            if response.status_code == 404:
                error_cls = ObjectNotFound
            else:
                error_cls = ClientError

        if response.request.method == 'HEAD':
            # There is no body, can only return None or raise exception
            if error_cls is not None:
                return error_cls("URL: %s" % response.request.url,
                                 {}, response.status_code)
            else:
                return None

        content = response.content
        if type(content) == bytes: # Python 3 fix
            content = content.decode('utf-8')
        d = json.loads(content)
        assert "status" in d, "Server response (%s) did not contain 'status' key, aborting" % serialized_data

        status = d["status"].lower()
        if status != "ok":
            assert status == 'error'
            assert 'response' in d
            response_dict = d['response']
            raise error_cls("URL: %s %r" % (response.request.url, response_dict),
                            response_dict, response.status_code)
        r = d['response']
        return SignuptoResponse(r['data'], r['next'], r['count'])


class Endpoint(object):

    def __init__(self, client, resource_name):
        self.client = client
        self.resource_name = resource_name

    def get(self, **kwargs):
        return self.client.make_request('GET', self.resource_name,
                                        params=kwargs)

    def post(self, **kwargs):
        return self.client.make_request('POST', self.resource_name,
                                        data=kwargs)

    def put(self, **kwargs):
        return self.client.make_request('PUT', self.resource_name,
                                        data=kwargs)

    def delete(self, **kwargs):
        return self.client.make_request('DELETE', self.resource_name,
                                        params=kwargs)

    def head(self, **kwargs):
        return self.client.make_request('HEAD', self.resource_name,
                                        params=kwargs)

    def get_all(self, **kwargs):
        """
        For requests that return lists in the 'data' attribute, and apply
        paging, this method will repeatedly follow the 'next' attribute to build
        up a full list, which is returned.
        """
        retval = []
        start = None
        kwargs = kwargs.copy()
        while True:
            if start is not None:
                kwargs['start'] = start
            response = self.get(**kwargs)
            retval.extend(response.data)
            if response.next is None:
                return retval
            else:
                start = response.next



for resource_name in API_RESOURCES:
    # Add the attributes to Client, with an unwrapper that removes the
    # 'ResponseHandler' object and simplifies the API

    def a_property(self, resource_name=resource_name):
        return Endpoint(self, resource_name)
    a_property.__name__ = resource_name

    setattr(Client, resource_name, property(a_property))
