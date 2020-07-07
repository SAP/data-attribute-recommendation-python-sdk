.. _retry:

Resilience and Error Recovery
=============================

Retrying HTTP Requests
**********************

The Data Attribute Recommendation client SDK will retry failed HTTP operations to some extent.

Because the Data Attribute Recommendation service uses a RESTful API, the standard HTTP semantics apply.

This makes it safe by default to retry requests using the GET or DELETE methods
since these methods are either safe or idempotent.

GET is what is called a `safe method`_ because repeating a GET request should not have any
side-effects. Accordingly, identical requests can be performed several times
without ill effects.

DELETE is not a safe method. It usually has side-effects such as deleting a resource
from a server.
However, DELETE is an `idempotent method`_. A request can be repeated several times and the result
will always be the same: the resource is gone. Note that all safe methods are also
idempotent!

These properties allow the Data Attribute Recommendation client SDK to retry many operations by default.

.. _safe method: https://tools.ietf.org/html/rfc7231#section-4.2.1
.. _idempotent method: https://tools.ietf.org/html/rfc7231#section-4.2.2


Retrying POST Requests
**********************

POST requests are not idempotent. They can not be retried, at least not
safely according to HTTP semantics.

For the Data Attribute Recommendation client SDK, this contains all *create_* methods since these are implemented
using POST. Where possible, the Data Attribute Recommendation client SDK provides a parameter to enable retry
behavior on the method itself. Before using this manual override to force retries for
POST, consider the trade-offs involved.

Consider the creation of a DatasetSchema using
:meth:`DataManagerClient.create_dataset_schema`. In a scenario where
the connection between client and server is dropped suddenly, the DatasetSchema may
have been created successfully.
On the client side, the Data Attribute Recommendation client SDK receives a "connection reset" error message
and is unaware that the new DatasetSchema has been created.
Implementing a naive retry simply based on HTTP semantics will lead to the creation
of a second DatasetSchema, because the HTTP client is not aware that the first
DatasetSchema was created.

A more advanced approach is to handle the error on the application level. In the
scenario described above, an additional request can be made to check if the desired
DatasetSchema was created. If the DatasetSchema is not there, a new request can be made.

If the risk of having an orphaned DatasetSchema is acceptable, then consider using the
*retry* parameter to :meth:`DataManagerClient.create_dataset_schema` to gain
additional robustness.


POST Requests which Acquire Limited Resources
-----------------------------------------------

Note that not all *create_* methods implement a *retry* parameter. The `create_deployment`
method can only be called once per model name. No two deployments can exist at the same
time for any model. For this reason, there is no naive retry implementation based on
repeating the initial failing request. Such an implementation cannot know if
the first request succeeded either completely or partially. If the first request was
successful, the second request will fail with a seemingly unrelated error related to
the model already being deployed.

See the documentation of the individual *create_* methods for details. For some tasks,
the Data Attribute Recommendation client SDK provides higher-level methods which implement application-level retry
including clean up of any singleton resources.

Before Connection is Established
--------------------------------

If an error occurs before the initial connection to the server is established (
i.e. connect timeout, DNS lookup problem), all HTTP methods are retried.

At this point, the server has not yet received the request. No unsafe side-effects
have happened yet, so it is safe to retry all HTTP methods.

Retrying Asynchronous Processes
*******************************

Data validation, model training and deployment are asynchronous processes which are
started via `create_` method calls and executed in the background. Their progress
and success status is exposed not via HTTP status codes in the response sent by
the API endpoint, but in the JSON body of the response.

For this reason, these operations cannot be retried at all by the HTTP-level retry implementation described above.

The Data Attribute Recommendation client SDK provides higher-level methods which can handle restarting the
individual processes, if desired.
