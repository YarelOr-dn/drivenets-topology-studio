system ntp authentication key 
------------------------------

**Minimum user role:** operator

When using NTP, the device synchronizes to a time source. If authentication is used, the synchronization is achieved only if the source carries the specified authentication keys. If the authentication fails, the local clock will not be updated.

To create an authentication key:

**Command syntax: authentication key [key-id]** password [password] type [authentication-type]

**Command mode:** config

**Hierarchies**

- system ntp


.. **Note**

	- If *password* is not specified, user will be requested to input unencrypted password and confirm.

	- no command removes the ntp server key

**Parameter table**

+---------------------+----------------------------------------------------------------------------------------------------+----------+---------+
| Parameter           | Description                                                                                        | Range    | Default |
+=====================+====================================================================================================+==========+=========+
| key-id              | Provide a unique key identifier that will serve to enable authentication on the NTP server.        | 1..65533 | \-      |
+---------------------+----------------------------------------------------------------------------------------------------+----------+---------+
| password            | An MD5 string. If a password is not specified, you will be prompted to enter an unencrypted value. | string   | \-      |
+---------------------+----------------------------------------------------------------------------------------------------+----------+---------+
| authentication-type | Optional. Defines the authentication method                                                        | MD5      | MD5     |
+---------------------+----------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ntp
	dnRouter(cfg-system-ntp)# authentication key 1 password enc-!@#$% type MD5
	dnRouter(cfg-system-ntp)# authentication key 2 password enc-!@#$%
	
	dnRouter(cfg-system-ntp)# authentication key 3 
	Enter password:
	Enter password for verification: 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ntp)# no authentication key 1

.. **Help line:** Configure system ntp authentication keys

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 5.1.0   | Command introduced                                         |
+---------+------------------------------------------------------------+
| 6.0     | Updated command syntax to "password" instead of "key-type" |
|         | Applied new hierarchy                                      |
+---------+------------------------------------------------------------+


