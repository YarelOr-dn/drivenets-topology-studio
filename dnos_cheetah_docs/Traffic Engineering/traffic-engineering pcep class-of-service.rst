traffic-engineering pcep class-of-service
-----------------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for outgoing PCEP packets:


**Command syntax: class-of-service [dscp-value]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Parameter table**

+----------------------+--------------------------------------------------------------------------------------------------+-----------+-------------+
|                      |                                                                                                  |           |             |
| Parameter            | Description                                                                                      | Range     | Default     |
+======================+==================================================================================================+===========+=============+
|                      |                                                                                                  |           |             |
| class-of-service     | The DSCP value that is used in the IP header to   classify the packet and give it a priority.    | 0..56     | 48          |
+----------------------+--------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# class-of-service 50

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-mpls-te-pcep)# no class-of-service


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+