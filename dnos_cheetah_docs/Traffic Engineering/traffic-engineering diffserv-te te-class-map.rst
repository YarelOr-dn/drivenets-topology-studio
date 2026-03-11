traffic-engineering diffserv-te te-class-map
--------------------------------------------

**Minimum user role:** operator

A te-class-map is the mapping between the class types, priorities, and traffic engineering classes.

To configure different levels of service to different class types:

#.	Enter te-class-map configuration mode

#.	Map class-type and tunnel priority to each TE class (see "mpls traffic-engineering diffserv-te te-class-map te-class").

To enter the te-class-map configuration hierarchy:

**Command syntax: te-class-map**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# te-class-map
	dnRouter(cfg-te-diffserv-te-class-map)#

**Removing Configuration**

To revert to the default mapping:
::

	dnRouter(cfg-mpls-te-diffserv)# no te-class-map


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+