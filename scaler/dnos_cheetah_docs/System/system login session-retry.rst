system login session-retry
--------------------------

**Minimum user role:** operator

To configure the number of allowed failed login attempts:

**Command syntax: session-retry [session-retry]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command sets the values to default

	- in case maximum number of attempts was tried, the connection should be silently rejected

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                                                                                                                                                                      | Range | Default |
+===============+==================================================================================================================================================================================================================================+=======+=========+
| session-retry | The number of consecutive login failed attempts allowed. If the maximum number of failed login attempts has been reached, the system will block further attempts for a configured time period. See system login session-holdoff. | 1..10 | 8       |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-retry 10 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-retry

.. **Help line:** configure maximum number of failed login retries.

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 6.0     | Command introduced    |
+---------+-----------------------+
| 13.0    | Changed default value |
+---------+-----------------------+

