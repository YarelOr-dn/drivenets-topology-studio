show dnos-internal routing fib-manager fpm queues
-------------------------------------------------

**Minimum user role:** viewer

To display fib-manager forwarding queue information:

**Command syntax: show dnos-internal routing fib-manager fpm queues {ncp [ncp-id] \| rib-manager}**

**Command mode:** operation

**Parameter table**

+----------------+-----------------------------------------------------+
|                |                                                     |
| Parameter      | Description                                         |
+================+=====================================================+
|                |                                                     |
| ncp-id         | Displays NCP queues information only                |
+----------------+-----------------------------------------------------+
|                |                                                     |
| rib-manager    | Displays RIB-manager connection information only    |
+----------------+-----------------------------------------------------+

**Example**
::

	dnRouter# show dnos-internal routing fib-manager fpm queues ncp 1
	NCP ID 1 (3), Name: ncp1_2985156096

	Queue                Size
	twamp delete         0
	routes low delete    0
	routes med delete    0
	routes high delete   0
	egress delete        0
	nexthop delete       0
	tunnel delete        0
	twamp add            0
	neighbors            0
	tunnel add           0
	nexthop add          0
	egress add           0
	egress acks          0
	routes high add      0
	routes med add       0
	routes low add       29046
	bfds                 0
	bfd status           0

	dnRouter# show dnos-internal routing fib-manager fpm queues rib-manager
	Connection to: RIB-Manager

	Queue                Size
	neighbor req         0
	mc event             0
	bfd status           0

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+


