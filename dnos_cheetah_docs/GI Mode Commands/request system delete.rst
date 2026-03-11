request system delete
---------------------

**Minimum user role:** viewer

Deletes DNOS databases, keys, certificates and logs on the node. To delete a DNOS router on the node:

**Command syntax: request system delete**

**Command mode:** GI

.. **Note**

 - Yes/no validation should exist for the operation.

**Parameter table**


**Example**
::

	gi# request system delete
	DNOS router database, keys and logs will be deleted from this node.
	Warning: Do you want to continue? (Yes/No) [No]?

	Deleting database...
	Deleting files...
	Done.


.. **Help line:** Delete DNOS router

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
