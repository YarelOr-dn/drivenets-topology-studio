traffic-engineering interface te-metric
----------------------------------------

**Minimum user role:** operator

By default, the traffic-engineering metric of a link matches the IGP metric assigned for the interface. The traffic-engineering metric is signalled by the IGP protocol as part of the TE parameters.

You can configure a te-metric that is different from the ipv4 metric to result in a traffic-engineering topology that is different than the IGP ipv4 unicast topology.

To set the te-metric:


**Command syntax: te-metric [metric]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering interface

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle
	
	- Bundle vlan

- The te-metric applies to ISIS level-2 only.

**Parameter table**

+---------------+------------------------------------------------------------+----------------+-------------+
|               |                                                            |                |             |
| Parameter     | Description                                                | Range          | Default     |
+===============+============================================================+================+=============+
|               |                                                            |                |             |
| metric        | Set the te-metric value for a given mpls-te   interface    | 1..16777215    | 10          |
+---------------+------------------------------------------------------------+----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1.1
	dnRouter(cfg-mpls-te-if)# te-metric 20


	dnRouter(cfg-protocols-mpls-te)# interface ge100-0/0/0
	dnRouter(cfg-mpls-te-if)# te-metric 30

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-mpls-te-if)# no te-metric


.. **Help line:** Configure traffic-engineering metric for the interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.1        | Command introduced    |
+-------------+-----------------------+