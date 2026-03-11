traffic-engineering diffserv-te cbts cos-te-map
-----------------------------------------------

**Minimum user role:** operator

A cos-te-map is the mapping of CoS to a Tunnel TE class.

To configure a cos-te-map, enter its configuration level:


**Command syntax: cos-te-map**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te cbts

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# cbts
	dnRouter(cfg-te-diffserv-cbts)# cos-te-map
	dnRouter(cfg-diffserv-cbts-cos-te-map)# 

**Removing Configuration**

To revert to the default mapping:
::

	dnRouter(cfg-te-diffserv-cbts)# no cos-te-map


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+