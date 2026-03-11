show ospf border-router
-----------------------

**Minimum user role:** viewer

To display OSPF border routers information for this area:

**Command syntax: show ospf** instance [ospf-instance-name] **border-router**

**Command mode:** operational


..
	**Internal Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+----------------------------------------------------------------+----------------------------+
| Parameter          | Description                                                    | Values                     |
+====================+================================================================+============================+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance. | configured instances names |
+--------------------+----------------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter# show ospf border-router

	OSPF Instance instance1
	============ OSPF router routing table ===========================
	O    2.2.2.2               [40] area: 0.0.0.0, ASBR
	                           via 12.12.4.2, ge100-0/0/4
	O    4.4.4.4               [40] area: 0.0.0.0, ASBR
	                           via 84.1.1.1, ge100-0/0/2


	dnRouter# show ospf instance instance1 border-router

	OSPF Instance instance1
	============ OSPF router routing table ===========================
	O    2.2.2.2               [40] area: 0.0.0.0, ASBR
	                           via 12.12.4.2, ge100-0/0/4
	O    4.4.4.4               [40] area: 0.0.0.0, ASBR
	                           via 84.1.1.1, ge100-0/0/2


.. **Help line:** Displays the OSPF border routers information for this area

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 18.2    | Added instance parameter |
+---------+--------------------------+
