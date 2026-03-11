show dnos-internal routing rib-manager fpm queues
-------------------------------------------------

**Minimum user role:** viewer

To display the forwarding path manager information:

**Command syntax: show dnos-internal routing rib-manager fpm queues**

**Command mode:** operation

**Example**
::

	dnRouter# dnos-internal routing rib-manager fpm queues
	Connection to FIB-Manager:

	Queue                Size
	routes low delete    42147
	routes med delete    0
	routes high delete   0
	nexthop delete       0
	tunnel delete        0
	neigbors             1
	tunnel add           0
	nexthop add          0
	routes high add      0
	routes med add       0
	routes low add       57920
	bfd sessions         0


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+


