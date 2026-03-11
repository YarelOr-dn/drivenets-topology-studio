system ftp
-----------

**Minimum user role:** operator

Use the following command to configure FTP server and client functionality:

**Command syntax: ftp [parameters]**

**Command mode:** config

**Hierarchies**

- system ftp


**Note**

- Notice the change in prompt.

.. - no command returns the ftp config to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)#


	

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-system-ftp)# no ftp

.. **Help line:** configure ftp server functionality.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+


