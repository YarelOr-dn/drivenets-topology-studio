show system yang-schemas 
-------------------------

**Minimum user role:** viewer

DNOS supports the Yet Another Next Generation (YANG) data modeling language used with NETCONF to provide automated and programmable network operations. YANG models the configuration and state data used by the NETCONF operations.

To display all available DNOS YANG models:

**Command syntax: show system yang-schemas**

**Command mode:** operational



**Example**
::

	dnRouter# show system yang-schemas
	
	supported yang list:
	| name          | version    |
	|---------------|------------|
	| dn-interfaces | 10.10.2018 |
	| dn-system     | 10.11.2018 |
	| dn-rpc        | 10.12.2018 |
		
	
	

.. **Help line:** show all available DNOS yang schemas in system.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


