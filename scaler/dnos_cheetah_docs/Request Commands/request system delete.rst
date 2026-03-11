request system delete
-----------------------

**Minimum user role:** admin

Deletes the DNOS router system.

- Stops DNOS services.

- Deletes DNOS database, keys, certificates, logs.


**Command syntax: request system delete**

**Command mode:** operational

**Example**
::

	dnRouter# request system delete
	DNOS router will be stopped, its database, keys and logs will be deleted.
	Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, deletion will run in background.
	Started system deletion
	Stopped DNOS on NCP 0...
	Deleted DNOS files on NCP 0...
	Stopped DNOS on NCP 1...
	Deleted DNOS files on NCP 1...
	Stopped DNOS on NCF1 0...
	Deleted DNOS files on NCF 0...
	...
	Stopped DNOS on NCC 1...
	Stopping DNOS on NCC 0...



**Note:**

-  Yes/no validation should exist for the operation.

.. **Help line:** Delete DNOS router.

.. **Parameter table:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
