show dnos-internal routing rib-manager rib-queues
-------------------------------------------------

**Minimum user role:** viewer

To display the rib-manager process queues information:

**Command syntax: show dnos-internal routing rib-manager rib-queues**

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing rib-manager rib-queues
	Queue                                    Size
	Connected, Kernel                        0
	Static routes                            0
	IGP (OSPF, OSPF6, IS-IS, LDP, RSVP)      0
	Privileged BGP                           0
	BGP                                      622
	Other                                    0

	Total                                    622

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+


