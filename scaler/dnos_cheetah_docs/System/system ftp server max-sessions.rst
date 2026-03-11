system ftp server max-sessions
------------------------------

**Minimum user role:** operator

Use the following command to configure maximum number of concurrent FTP sessions to FTP server:

**Command syntax: server max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- The 'no max-sessions' returns the number of maximum sessions to its default value.

.. - no command returns the number of maximum sessions to default

**Parameter table**

+--------------+---------------------------------------------------------+-------+---------+
| Parameter    | Description                                             | Range | Default |
+==============+=========================================================+=======+=========+
| max-sessions | Configure the maximum number of concurrent FTP sessions | 1..32 | 10      |
+--------------+---------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)# max-sessions 5




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no max-sessions

.. **Help line:** configure maximum number of concurrent FTP sessions to FTP server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
