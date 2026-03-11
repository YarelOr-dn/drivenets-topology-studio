system login session-holdoff
----------------------------

**Minimum user role:** operator

To configure the amount of time that the system will block login attempts after the maximum number of allowed failed attempts is reached:

**Command syntax: session-holdoff [session-holdoff]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command sets the values to default

	- in case maximum number of attempts was tried, the connection should be silently rejected.

**Parameter table**

+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                                                                                                   | Range | Default |
+=================+===============================================================================================================================================================+=======+=========+
| session-holdoff | The amount of time (in minutes) to wait after the maximum number of failed login attempts is reached, before the system will allow to attempt to login again. | 3..15 | 10      |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-holdoff 5
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-holdoff

.. **Help line:** configure holdoff time in case the maximum number of failed login retries has been reached.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

