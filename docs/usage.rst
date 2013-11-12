========
Usage
========

These docs assume familiarity with the `API docs for sign-up.to
<https://dev.sign-up.to/documentation/reference/latest/>`_, which provide most
of the details for endpoints, parameters etc.

Quickstart::

   >>> from signupto import Client, HashAuthorization
   >>> c = Client(auth=HashAuthorization(company_id=1234, user_id=4567,
   ...                                   api_key='e4cf7fe3b764a18c04f6792c09e3325d'))
   >>> c.subscription.get(list_id=7890).data

   [{u'cdate': 1374769049,
     u'confirmationredirect': u'',
     u'confirmed': True,
     u'id': 36154421,
     u'list_id': 7890,
     u'mdate': 1374769049,
     u'source': u'import',
     u'subscriber_id': 9180894},
    {u'cdate': 1374769049,
     u'confirmationredirect': u'',
     u'confirmed': True,
     u'id': 13654428,
     u'list_id': 7890,
     u'mdate': 1374769040,
     u'source': u'import',
     u'subscriber_id': 9186895}]


Authorization
=============

Hash authorization::

   >>> from signupto import Client, HashAuthorization
   >>> c = Client(auth=HashAuthorization(company_id=1234, user_id=4567,
   ...                                   api_key='e4cf7fe3b764a18c04f6792c09e3325d'))



Token authorization::

   >>> from signupto import Client, TokenAuthorization
   >>> c = Client(auth=TokenAuthorization(username='joe', password='my_secret'))

This will do an unauthenticated API call to get the token, which will be used in
subsequent API calls. If you want to get the actual token returned, along with
the expiry timestamp, for storage and re-use, they can be found as attributes on
the ``TokenAuthorization`` instance, after it has been passed to the ``Client``
constructor::

   >>> token_auth = TokenAuthorization(username='joe', password='my_secret')
   >>> c = Client(auth=token_auth)
   >>> token, expiry = token_auth.token, token_auth.expiry

And then to re-use later::

   >>> token_auth_2 = TokenAuthorization()
   >>> token_auth_2.token = token
   >>> token_auth_2.initialized = True
   >>> c = Client(auth=token_auth_2)


API calls
=========

Client instances have attributes representing all the resources/endpoints. The
spelling of the attribute is the same as the path for the endpoint
e.g. ``subscription``, ``clickAutomation``.

Each endpoint then has methods for the HTTP verbs: get(), post(), put(),
delete() and head().

Parameters to the endpoint are passed as keyword arguments to these methods.

Endpoints and their parameters are described in the sign-up.to docs here:
https://dev.sign-up.to/documentation/reference/latest/endpoints/

These methods return a ``SignuptoResponse`` object, which contains the
'response' attribute of the API call, that is, an object with these attributes:

* ``data`` - the data returned by the API call, converted to native Python
  objects e.g. a Python dictionary containing list information, or an array.
  The ``signupto`` library does not convert the data beyond converting into
  native Python types.

* ``next`` - value representing the resource following the last returned resource.

* ``count`` - the number of resources returned.

Usually you will just need the ``data`` attribute. See
https://dev.sign-up.to/documentation/reference/latest/making-requests/response-format/
for more information.


Example::

    >>> c.subscription.post(list_id=1234, subscriber_id=4567)

    SignuptoResponse(data={u'confirmed': False, u'mdate': 1384265219,
                           u'confirmationredirect': u'', u'subscriber_id': 4567,
                           u'source': u'api', u'cdate': 1384265219, u'list_id': 1234,
                           u'id': 19486109}, next=None, count=1)


As there is no response dictionary for ``HEAD`` verbs, the ``head()`` method
does not return a ``SignuptoResponse``, but instead returns None. It will raise
an error like the other calls for HTTP codes in 4XX range.

Errors
======

Errors returned in JSON documents by the server will raise
``signupto.ClientError``. For example::


    >>> c = Client(auth=HashAuthorization(company_id=1234, user_id=4567,
    ...                                   api_key='oops'))
    >>> c.list.get()

    ClientError: {u'message': u'Bad signature:
    9ec621a4c27dcb28bdb2148f1475f990f7adfbd6', u'code': 401, u'subcode': None,
    u'additional_information': u'GET /v0/list\\r\\nDate: Tue, 12 Nov 2013
    14:24:58 GMT\\r\\nX-SuT-CID: 28711\\r\\nX-SuT-UID: 6235\\r\\nX-SuT-Nonce:
    h91eq7qwh43go4tpu20hiaira2mfuu7yqf8e4t'}


The dictionary is stored on the exception object in the attribute ``error_info``.

When the error has code 404, indicating something not found, a subclass of
``ClientError``, ``ObjectNotFound``, is used instead. This can be especially
useful when you are applying filters such that there are no matching objects,
which is often not an error condition for your application, so needs to be
handled differently::


    from signupto import ObjectNotFound

    try:
        unconfirmed = c.subscription.get(list_id=1234, confirmed=False).data
    except ObjectNotFound:
        unconfirmed = []


