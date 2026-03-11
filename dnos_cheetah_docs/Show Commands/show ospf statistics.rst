show ospf statistics
--------------------

**Minimum user role:** viewer

The show ospf statistics command displays OSPF packet type statistics globally or per interface when an interface is provided.

**Command syntax: show ospf** instance [ospf-instance-name] **statistics** interface [interface-name]

**Command mode:** operational




**Parameter table**

+--------------------+--------------------------------------------------------------------+---------------------------------------------------+---------+
| Parameter          | Description                                                        | Range                                             | Default |
+====================+====================================================================+===================================================+=========+
| interface-name     | The name of the specified interface                                | ge<interface speed>-<A>/<B>/<C>                   | all     |
|                    |                                                                    | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|         |
|                    |                                                                    | bundle-<bundle id>                                |         |
|                    |                                                                    | bundle-<bundle id>.<sub-interface id>             |         |
|                    |                                                                    | lo<lo-interface id>                               |         |
+--------------------+--------------------------------------------------------------------+---------------------------------------------------+---------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance.     | Configured instances names                        | all     |
+--------------------+--------------------------------------------------------------------+---------------------------------------------------+---------+

**Example**
::

	dnRouter# show ospf statistics

	Ospf Instance instance1
	OSPF Statistics on all interfaces:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |      12432     |      12324    |
		| DB Description     |        984     |        619    |
		| Link state request |        432     |        391    |
		| Link state update  |        312     |        543    |
		| Link State Ack     |        129     |        201    |


	dnRouter# show ospf instance instance1 statistics

	Ospf Instance instance1
	OSPF Statistics on all interfaces:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |      12432     |      12324    |
		| DB Description     |        984     |        619    |
		| Link state request |        432     |        391    |
		| Link state update  |        312     |        543    |
		| Link State Ack     |        129     |        201    |


	dnRouter# show ospf statistics interface ge100-1/2/2.123

	OSPF Statistics on interface ge100-1/2/2.123:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |       3245     |       1024    |
		| DB Description     |         75     |         69    |
		| Link state request |         94     |         31    |
		| Link state update  |         29     |        	53    |
		| Link State Ack     |         84     |         42    |


	dnRouter# show ospf instance instance1 statistics interface ge100-1/2/2.123

	OSPF Statistics on interface ge100-1/2/2.123:

		| OSPF Packet type   |    Rx[pkts]    |    Tx[pkts]   |
		+--------------------+----------------+---------------+
		| Hello              |       3245     |       1024    |
		| DB Description     |         75     |         69    |
		| Link state request |         94     |         31    |
		| Link state update  |         29     |        	53    |
		| Link State Ack     |         84     |         42    |

.. **Help line:** Displays OSPF packet type counters.

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 18.2    | Added instance parameter |
+---------+--------------------------+
