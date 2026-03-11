clear telnet session
--------------------

**Minimum user role:** operator

To terminate active telnet sessions:

**Command syntax: clear telnet session [session-id]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**


**Parameter table**

+------------+---------------------------------------------------------------------------+
| Parameter  | Description                                                               |
+============+===========================================================================+
| session-id | Any active session id presented by "show system telnet sessions" commands |
+------------+---------------------------------------------------------------------------+

**Example**
::

	dnRouter# clear telnet session 57
	Telnet session userName@pts2 was successfully terminated

	dnRouter# clear telnet session 131
	Telnet session userName@pts2 was successfully terminated


.. **Help line:** Clear active telnet session


**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 13.1        | Command introduced                          |
+-------------+---------------------------------------------+