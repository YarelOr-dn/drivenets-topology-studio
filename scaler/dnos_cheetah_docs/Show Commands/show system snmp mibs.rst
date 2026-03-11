show system snmp mibs
---------------------

**Minimum user role:** viewer

The following command displays a list of the available SNMP mibs.

**Command syntax: show system snmp mibs**

**Command mode:** operational



**Example**
::

	dnRouter# show system snmp mibs
	
	| OID                          | Object Name                  |
	|------------------------------|------------------------------|
	| 1.3.6.1.2.1.11.1             | snmp.1                       |
	| 1.3.6.1.4.1.99.12.35.1.1.1.1 | enterprises.99.12.35.1.1.1.1 |
	| 1.3.6.1.6.3.1.1.6.1          | internet.3.6.1.6.3.1.1.6.1   |
	

.. **Help line:** show snmp mibs

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


