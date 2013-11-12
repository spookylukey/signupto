===============================
signupto
===============================

Minimalist client library for the sign-up.to HTTP API - http://sign-up.to

* Free software: BSD license


Status
======

This is alpha software. It works, and covers the complete sign-up.to HTTP API,
but the API is not yet finalized, especially in the area of error handling.

There are also no automated tests. (It is a bit tricky to test as this is a thin
wrapper around drest, and you really have to test a client library like this
against the actually web service, which has no sandbox).

Usage
=====

.. code-block:: python

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


You can also do token authorisation::

    >>> c = Client(auth=TokenAuthorization(username='joe', password='my_secret'))


Client instances have attributes representing all the resources. The spelling of
the attribute is the same as the path for the endpoint e.g. ``subscription``,
``clickAutomation``.

Each endpoint then has methods for the HTTP verbs: get(), post(), put(), delete() and head().

Parameters to the endpoint are passed as keyword arguments to these methods. Example::

    >>> c.subscription.post(list_id=1234, subscriber_id=4567)
    SignuptoReponse(data={u'confirmed': False, u'mdate': 1384265219,
                          u'confirmationredirect': u'', u'subscriber_id': 4567,
                          u'source': u'api', u'cdate': 1384265219, u'list_id': 1234,
                          u'id': 19486109}, next=None, count=1)


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


The dictionary is stored on the exception object in the attribute 'error_info'.

When the error has code 404, indicating something not found, a subclass of
``ClientError``, ``ObjectNotFound``, is used instead. This can be especially
useful when you are applying filters with the result is that there are no
matching objects, which is often not an error condition for your application, so
needs to be handled differently::


    try:
        unconfirmed = c.subscription.get(list_id=1234, confirmed=False).data
    except ObjectNotFound:
        unconfirmed = []


