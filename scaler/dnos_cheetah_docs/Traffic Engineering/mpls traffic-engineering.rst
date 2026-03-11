mpls traffic-engineering
------------------------

**Minimum user role:** operator

Traffic engineering (TE) is a method for the effective use of available network resources by controlling the path that data packets follow across the MPLS network. TE is based on building label-switched paths (LSPs) among routers using RSVP and creating administrative groups that you can either include or exclude in the traffic engineering database.

TE requires an IGP for routing decisions. NCR TE relies on IS-IS. Therefore, only interfaces on which IS-IS is enabled can be used for TE.

The TE configuration commands allow you to enable TE on an interface, and to create admin-group-maps for grouping links into classes.

To set traffic engineering parameters, you must first enter MPLS traffic engineering configuration mode. 


**Command syntax: mpls traffic-engineering**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# 

**Removing Configuration**

To remove all traffic engineering configurations:
::

	dnRouter(cfg-protocols-mpls)# no traffic-engineering


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+