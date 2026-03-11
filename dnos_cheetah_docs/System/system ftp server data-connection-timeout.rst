system ftp server data-connection-timeout
-----------------------------------------

**Minimum user role:** operator

Use the following command to configure the timeout (in minutes), which is the maximum amount of time permitted for data transfers to stall without progress:

**Command syntax: server data-connection-timeout [timeout]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- The 'no data-connection-timeout' returns the number to its default value.

.. - The configured value is the minimum amount of time data connection is allowed before being disconnected. The maximum amount of time will not exceed twice the configured value for data-connection-timeout.

	- no command returns the number of data-connection-timeout to default

**Parameter table**

+-------------------------+------------------------------------+-------+---------+
| Parameter               | Description                        | Range | Default |
+=========================+====================================+=======+=========+
| data-connection-timeout | Configure the timeout (in minutes) | 0..90 | 5       |
+-------------------------+------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)# data-connection-timeout 30

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no data-connection-timeout

.. **Help line:** configure the minimal timeout in minutes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
