show system snmp users
----------------------

**Minimum user role:** viewer

The following command displays a list of the configured SNMP v3 users.



**Command syntax: show system snmp users**

**Command mode:** operational



**Example**
::

	dnRouter# show system snmp users
	
	| User          | Authentication | Encryption | View        |
	|---------------+----------------+------------+-------------|
	| MySnmpUserv1  | md5            | none       | viewdefault |
	| MySnmpUserv2  | none           | none       | viewdefault |
	| MySnmpUserv3  | sha            | des        | viewall     |
	

.. **Help line:** show system snmp users

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Updated example to show view column |
+---------+-------------------------------------+


