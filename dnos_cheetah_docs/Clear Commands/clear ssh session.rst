clear ssh session
------------------

**Minimum user role:** operator

To terminate an active SSH session:

**Command syntax: clear ssh session [session-id]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+------------+-----------------------------------------------------------------------+----------+--------------+
| Parameter  | Values                                                                |   Range  |Default       |
+============+=======================================================================+==========+==============+
| session-id | Any active session-id presented by "show system ssh sessions" command | \-       | \-           |
+------------+-----------------------------------------------------------------------+----------+--------------+

**Example**
::

	dnRouter# clear ssh session 57
	SSH session MyUserName@pts2 was successfully terminated

	dnRouter# clear ssh session 131
	SSH session MyUserName@pts2 was successfully terminated


.. **Help line:** Clear active ssh session

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 5.1.0       | Command introduced    |
+-------------+-----------------------+