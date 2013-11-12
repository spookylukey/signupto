#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import random
import string

try:
    from sha import new as sha1
except ImportError:
    from hashlib import sha1
from six.moves.urllib import parse as urllib_parse

import drest
import drest.exc
import drest.request
import drest.serialization
import drest.resource

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

SignuptoResponse = namedtuple('SignuptoReponse', 'data next count')



class ClientError(ValueError):
    """
    Indicates error made by programmer using this library.
    Used when the server returns a JSON document indicating the error.
    """
    def __init__(self, message, error_info):
        super(ValueError, self).__init__(message)
        self.error_info = error_info


class ObjectNotFound(ClientError):
    pass


class SignuptoSerializationHandler(drest.serialization.JsonSerializationHandler):
    """
    JSON serialization handler, that also unwraps a layer of the returned
    data dictionary for convenience.
    """
    def deserialize(self, serialized_data):
        if len(serialized_data) == 0:
            # For HEAD responses
            return serialized_data
        d = super(SignuptoSerializationHandler, self).deserialize(serialized_data)
        assert "status" in d, "Server response (%s) did not contain 'status' key, aborting" % serialized_data
        if d["status"].lower() != "ok":
            if d['status'].lower() == "error" and 'response' in d:
                if d['response'].get('code', None) == 404:
                    cls = ObjectNotFound
                else:
                    cls = ClientError
                raise cls("%r" % d['response'], d['response'])
            raise AssertionError("Unexpected status '%s', aborting" % d['status'])
        r = d['response']
        return SignuptoResponse(r['data'], r['next'], r['count'])


class SignuptoResourceHandler(drest.resource.RESTResourceHandler):

    # Need to add 'head' which is not in RESTResourceHandler. Copy-paste job.
    def head(self, resource_id=None, params=None):
        if params is None:
            params = {}
        if resource_id:
            path = '/%s/%s' % (self.path, resource_id)
        else:
            path = '/%s' % self.path

        # We need to force params into query string, which drest doesn't support
        params = self.filter(params)
        url = urllib_parse.urlunparse(('', '', path, '', '&'.join('%s=%s' % (k, v) for k, v in params.items()), ''))
        try:
            response = self.api.make_request('HEAD', url,
                                             None)
        except drest.exc.dRestRequestError as e:
            msg = "%s (resource: %s, id: %s)" % (e.msg, self.name,
                                                 resource_id)
            raise drest.exc.dRestRequestError(msg, e.response)

        return response

    # Make the interface standard by not requiring resource_id, and allowing for
    # other types of query - e.g. see
    # https://dev.sign-up.to/documentation/reference/latest/endpoints/subscription/
    # which allows deleting by different parameters
    def delete(self, params=None):
        if params is None:
            params = {}
        if 'id' in params:
            resource_id = params.pop('id')
            path = "/%s/%s" % (self.path, resource_id)
        else:
            path = '/%s' % self.path

        try:
            response = self.api.make_request('DELETE', path, params)
        except drest.exc.dRestRequestError as e:
            msg = "%s (resource: %s, id: %s)" % (e.msg, self.name,
                                                 resource_id)
            raise drest.exc.dRestRequestError(msg, e.response)

        return response

    # Again, we want a consistent API so don't require resource_id
    def put(self, params=None):
        if params is None:
            params = {}

        params = self.filter(params)
        path = '/%s' % self.path

        try:
            response = self.api.make_request('PUT', path, params)
        except drest.exc.dRestRequestError as e:
            msg = "%s (resource: %s, id: %s)" % (e.msg, self.name,
                                                 resource_id)
            raise drest.exc.dRestRequestError(msg, e.response)

        return response


class SignuptoRequestHandler(drest.request.RequestHandler):
    class Meta:
        serialize = True
        deserialize = True
        serialization_handler  = SignuptoSerializationHandler

    """
    Request handler that can do include sign-up.to authentication methods
    (by delegating to other classes).
    """
    def __init__(self, **kwargs):
        signupto_auth = kwargs.pop('signupto_auth', None)
        if signupto_auth is None:
            signupto_auth = NoAuthorization()
        self.signupto_auth = signupto_auth
        super(SignuptoRequestHandler, self).__init__(**kwargs)

    def make_request(self, method, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {}
        base_handler = super(SignuptoRequestHandler, self)
        return self.signupto_auth.make_authorized_request(base_handler, method, url, params=params, headers=headers)


class SignuptoAPI(drest.API):
    class Meta:
        trailing_slash = False
        extra_headers = {'Accept': 'application/json'}
        request_handler = SignuptoRequestHandler
        resource_handler = SignuptoResourceHandler


class NoAuthorization(object):
    def make_authorized_request(self, handler, method, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {}
        return handler.make_request(method, url, params=params, headers=headers)


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

    def initialized(self, version=None):
        self.version = version # Need for canonical string

    def make_nonce(self):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(40))

    def make_authorized_request(self, handler, method, url, params=None, headers=None):
        if params is None:
            params = {}
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
        return handler.make_request(method, url, params=params, headers=headers)


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

    def make_authorized_request(self, handler, method, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {}
        headers['Authorization'] = "SuTToken %s" % self.token
        return handler.make_request(method, url, params=params, headers=headers)


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

    def __init__(self, version="0", auth=None):
        if hasattr(auth, 'initialize') and not getattr(auth, 'initialized', False):
            auth.initialize(version=version)

        api = SignuptoAPI(
            baseurl='https://api.sign-up.to/v%s/' % version,
            signupto_auth=auth, # will be passed to RequestHandler __init__
            )

        for resource_name in API_RESOURCES:
            api.add_resource(resource_name)

        self.api = api


class Endpoint(object):
    # This provides an API similar to ResourceHandler, but simplified to allow
    # the data dictionary to be passed keyword arguments, and returns the
    # SignuptoResponse rather than the ResponseHandler object.

    # This simplifies:
    #   client.api.foo.get(dict(option='bar')).data.data
    # to:
    #   client.foo.get(option='bar').data

    def __init__(self, drest_api, resource_name):
        self.drest_api = drest_api
        self.resource_name = resource_name

    def get(self, **kwargs):
        return getattr(self.drest_api, self.resource_name).get(params=kwargs).data

    def post(self, **kwargs):
        return getattr(self.drest_api, self.resource_name).post(params=kwargs).data

    def put(self, **kwargs):
        return getattr(self.drest_api, self.resource_name).put(params=kwargs).data

    def delete(self, **kwargs):
        return getattr(self.drest_api, self.resource_name).delete(params=kwargs).data

    def head(self, **kwargs):
        return getattr(self.drest_api, self.resource_name).head(params=kwargs).data



for resource_name in API_RESOURCES:
    # Add the attributes to Client, with an unwrapper that removes the
    # 'ResponseHandler' object and simplifies the API

    def a_property(self, resource_name=resource_name):
        return Endpoint(self.api, resource_name)
    a_property.__name__ = resource_name

    setattr(Client, resource_name, property(a_property))
