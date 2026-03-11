clear netconf session 
----------------------

**Minimum user role:** operator

To clear active netconf sessions:

**Command syntax: clear netconf session** [session-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

- By default, all sessions removed when session-id is not specified. 

**Parameter table:**

+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+
|               |                                                                                                                 |                                                                   |             |
| Parameter     | Description                                                                                                     | Range                                                             | Default     |
+===============+=================================================================================================================+===================================================================+=============+
|               |                                                                                                                 | Any active session-id displayed by "show system netconf sessions" |             |
| session-id    | Enter a specific session ID to clear (terminate). If you do not specify an ID, all sessions will be cleared.    |                                                                   | \-          |
+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear netconf session 57
	NETCONF session MyUserName was successfully terminated
	
	dnRouter# clear netconf session 131
	NETCONF session MyUserName2 was successfully terminated
		
	dnRouter# clear netconf session
	NETCONF session MyUserName was successfully terminated
	NETCONF session MyUserName2 was successfully terminated


.. **Help line:** Clear active netconf session

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+