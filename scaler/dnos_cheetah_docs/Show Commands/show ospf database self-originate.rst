show ospf database self-originate
---------------------------------

**Minimum user role:** viewer

To display the OSPF self originated link state:

**Command syntax: show ospf** instance [ospf-instance-name] **database self-originate**

**Command mode:** operational


..
	**Internal Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+----------------------------------------------------------------+----------------------------+
| Parameter          | Description                                                    | Values                     |
+====================+================================================================+============================+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance  | Configured instances names |
+--------------------+----------------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter# show ospf database self-originate

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)

	                Router Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum  Link count
	100.70.1.45     100.70.1.45     1292 0x800000ae 0xc740 8

	                Net Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum
	10.170.1.65     100.70.1.45     1222 0x80000010 0x406d


	dnRouter# show ospf instance instance1 database self-originate

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)

	                Router Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum  Link count
	100.70.1.45     100.70.1.45     1292 0x800000ae 0xc740 8

	                Net Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum
	10.170.1.65     100.70.1.45     1222 0x80000010 0x406d


.. **Help line:** OSPF self originated information

**Command History**

+-------------+--------------------------+
| Release     | Modification             |
+=============+==========================+
| 11.6        | Command introduced       |
+-------------+--------------------------+
| 18.2        | Added instance parameter |
+-------------+--------------------------+
