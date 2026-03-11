system ftp server idle-session-timeout
--------------------------------------

**Minimum user role:** operator

Use the following command to configure the timeout (in minutes), which is the maximum amount of time permitted for a remote client to spend between FTP commands:

**Command syntax: server idle-session-timeout [timeout]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- The 'no idle-session-timeout' returns the number to its default value.

.. - no command returns the number of idle-session-timeout to default

**Parameter table**

+----------------------+------------------------------------+-------+---------+
| Parameter            | Description                        | Range | Default |
+======================+====================================+=======+=========+
| idle-session-timeout | Configure the timeout (in minutes) | 0..90 | 30      |
+----------------------+------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)# idle-session-timeout 30




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no idle-session-timeout

.. **Help line:** configure the timeout in minutes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
