clear ftp session
------------------

**Minimum user role:** operator

To clear ftp sessions:

**Command syntax: clear ftp session [session-id]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. **Parameter table:**

+------------+-----------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                           | Range | Default |
+------------+-----------------------------------------------------------------------+-------+---------+
| session-id | Any active session-id presented by "show system ftp sessions" command | /-    | /-      |
+------------+-----------------------------------------------------------------------+-------+---------+


**Example**
::

	dnRouter# clear ftp session 57
	FTP session MyUserName@pts2 was successfully terminated

	dnRouter# clear ftp session 131
	FTP session MyUserName@pts2 was successfully terminated


.. **Help line:** Clear active ftp session

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 11.2        | Command introduced    |
+-------------+-----------------------+