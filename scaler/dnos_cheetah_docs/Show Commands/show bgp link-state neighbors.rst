show bgp link-state neighbors
-----------------------------

**Minimum user role:** viewer

BGP Link-State (LS) is an Address Family Identifier (AFI) that carries IGP link-state database through BGP

To display detailed information on TCP and BGP neighbor connections:

**Command syntax: show bgp link-state neighbors** [neighbor-address]

**Command mode:** operational


..
	**Internal Note**

	- set 'neighbor-address' to display information for a specific neighbor, otherwise displays for all link-state neighbor sessions

**Parameter table**

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter         | Description                                                                                                                                             | Range                       |
+===================+=========================================================================================================================================================+=============================+
| neighbor-address  | Neighbor address                                                                                                                                        | A.B.C.D                     |
|                   |                                                                                                                                                         | xx:xx::xx:xx                |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp link-state neighbors
	
	dnRouter# show bgp link-state neighbors 1.1.1.1
	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

