routing-options load-balancing 
-------------------------------

**Minimum user role:** operator

Load balancing is the ability to spread traffic over multiple paths to a destination. Typically, when the router learns multiple paths to the same network via multiple routing protocols, it installs in its routing table only one route: the route with the lowest administrative distance. Similarly, when the router learns multiple paths via the same routing protocol (i.e. with the same administrative distance), it selects the path with the lowest cost to the destination. Load balancing can occur when the router is able to install multiple paths with the same administrative distance and cost to the destination.

When there are equal-cost paths to a destination, the router runs a hash algorithm that uses the packet's 3-tuple or 5-tuple (configurable) to select one of the paths for the packet, thus ensuring flow-based routing.

For the router to distribute the traffic over multiple paths, you need to:

- Configure the protocols' maximum-paths attribute to a value greater than 1. This will allow the protocol to install multiple equal cost paths in the routing table (see bgp address-family maximum-paths and isis instance address-family maximum-paths).

- Configure the flow type (3-tuple or 5-tuple) to be used for path selection (see routing-options load-balancing flow).

To enter load-balancing configuration mode:

**Command syntax: load-balancing**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Unequal cost and per-prefix load balancing are not supported.

- Notice the change in prompt.

.. -  no command returns all load-balancing configurations to their default state

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# load-balancing
	dnRouter(cfg-routing-option-lb)# 
	
	

**Removing Configuration**

To revert to all load-balancing configurations to their default value: 
::

	dnRouter(cfg-routing-option)# no load-balancing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


