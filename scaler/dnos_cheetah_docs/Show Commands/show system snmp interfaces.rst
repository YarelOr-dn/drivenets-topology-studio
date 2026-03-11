show system snmp interfaces
---------------------------

**Minimum user role:** viewer

This command is applicable to the following interfaces:

physical interfaces, logical interfaces (sub-interfaces), bundle interfaces, bundle sub-interfaces, loopback interfaces, mgmt0 interfaces

The following command displays a list of interfaces in the system with their if-index.

**Command syntax: show system snmp interfaces**

**Command mode:** operational



.. **Note**

	- show command intended to show aggregated ifindex in one table

**Example**
::

	dnRouter# show system snmp interfaces
	
	| Interface         | ifIndex |
	|-------------------+---------|
	| bundle-1          | 1       |
	| bundle-1.200      | 20      |
	| ge10-0/0/0        | 10      |
	| ge10-1/0/0.100    | 40      |
	| mgmt-0/0          | 100     |
	| lo1               | 30      |

.. **Help line:** show system snmp interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


