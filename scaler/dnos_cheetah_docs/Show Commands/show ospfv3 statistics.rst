show ospfv3 statistics
----------------------

**Minimum user role:** viewer

The show ospf statistics command displays OSPF packet type statistics globally or per interface when an interface is provided.



**Command syntax: show ospfv3 statistics** interface [interface-name]

**Command mode:** operational




**Parameter table**

+----------------+-------------------------------------+---------------------------------------------------+---------+
| Parameter      | Description                         | Range                                             | Default |
+================+=====================================+===================================================+=========+
| interface-name | The name of the specified interface | ge<interface speed>-<A>/<B>/<C>                   | all     |
|                |                                     | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|         |
|                |                                     | bundle-<bundle id>                                |         |
|                |                                     | bundle-<bundle id>.<sub-interface id>             |         |
|                |                                     | lo<lo-interface id>                               |         |
+----------------+-------------------------------------+---------------------------------------------------+---------+

**Example**
::

	dnRouter# show ospfv3 statistics

	OSPFv3 Statistics on all interfaces:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |      12432     |      12324    |
		| DB Description     |        984     |        619    |
		| Link state request |        432     |        391    |
		| Link state update  |        312     |        543    |
		| Link State Ack     |        129     |        201    |


	dnRouter# show ospfv3 statistics interface ge100-1/2/2.123

	OSPFv3 Statistics on interface ge100-1/2/2.123:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |       3245     |       1024    |
		| DB Description     |         75     |         69    |
		| Link state request |         94     |         31    |
		| Link state update  |         29     |        	53    |
		| Link State Ack     |         84     |         42    |

.. **Help line:** Displays OSPFv3 packet type counters.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
