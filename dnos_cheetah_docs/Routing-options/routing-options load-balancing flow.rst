routing-options load-balancing flow
------------------------------------

**Minimum user role:** operator

To instruct the router which network headers to use to select one of multiple equal-cost paths to the destination for flow-based routing:

**Command syntax: flow [flow]**

**Command mode:** config

**Hierarchies**

- routing-options load-balancing

**Note**

- For fragmented packets, 3-tuple is used regardless of the configuration.

.. -  no command returns flow to its default state

**Parameter table**

+-----------+-----------------------------------------------------------+-----------------------------------------------+---------+
| Parameter | Description                                               | Range                                         | Default |
+===========+===========================================================+===============================================+=========+
| flow      | The network headers to use for flow-based load-balancing. | 3-tuple: Ethernet, MPLS, and IP               | 5-tuple |
|           |                                                           | 5-tuple: Ethernet, MPLS, IP, TCP/UDP, and GTP |         |
+-----------+-----------------------------------------------------------+-----------------------------------------------+---------+

**Example**
::

	dnRouter# configure 
	dnRouter(cfg)# routing-options 
	dnRouter(cfg-routing-option)# load-balancing 
	dnRouter(cfg-routing-option-lb)# flow 3-tuple 
	 
	 

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-routing-option-lb)# no flow 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


