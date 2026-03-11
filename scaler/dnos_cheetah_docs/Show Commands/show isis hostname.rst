show isis hostname
------------------

**Minimum user role:** viewer

To display the mapping between the IS-IS system-ID and the IS-IS dynamic hostname:



**Command syntax: show isis** instance [isis-instance-name] **hostname**

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

**Parameter table**

+--------------------+------------------------------------------------------------+--------+
| Parameter          | Description                                                | Range  |
+====================+============================================================+========+
| isis-instance-name | Filters the hostname mapping to a specific IS-IS instance. | String |
+--------------------+------------------------------------------------------------+--------+

**Example**
::

	dnRouter# show isis hostname
	Level  System ID       Dynamic Hostname
	L2   * 1111.1111.1111  ROUTER_1
	L2     6801.0001.0000  ROUTER_2
	
	Instance CORE152:
	Level  System ID       Dynamic Hostname
	L2   * 1111.1111.1111  ROUTER_1
	L2     0000.0003.0001  vROUTER_1
	L2     6601.0001.0000  ROUTER_4
	L2     6701.0001.0000  ROUTER_3-1
	L2     6701.0002.0000  ROUTER_3-2
	L2     6701.0003.0000  ROUTER_3-3
	L2     8888.8888.8888  ROUTER_4
	L2     9999.9999.9999  ROUTER_5
	
	
	dnRouter# show isis instance CORE152 hostname
	Instance CORE152:
	Level  System ID       Dynamic Hostname
	L2   * 1111.1111.1111  ROUTER_1
	L2     0000.0003.0001  vROUTER_1
	L2     6601.0001.0000  ROUTER_4
	L2     6701.0001.0000  ROUTER_3-1
	L2     6701.0002.0000  ROUTER_3-2
	L2     6701.0003.0000  ROUTER_3-3
	L2     8888.8888.8888  ROUTER_4
	L2     9999.9999.9999  ROUTER_5
	
	
	

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


