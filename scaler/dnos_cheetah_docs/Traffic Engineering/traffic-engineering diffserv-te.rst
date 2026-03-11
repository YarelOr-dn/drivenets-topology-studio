traffic-engineering diffserv-te
-------------------------------

**Minimum user role:** operator

Differentiated services (DiffServ)-aware traffic engineering enables to guarantee different levels of service and bandwidth to different class types over the MPLS network. 

To achieve this, follow these general steps:

#.	Enter DiffServ-te configuration mode (see how below).

#.	Enable DiffServ-te on the system (see "mpls traffic-engineering diffserv-te admin-state")

#.	Select a TE bandwidth-model (RDM) (see "mpls traffic-engineering diffserv-te bandwidth-model")

#.	Enter te-class-map configuration mode (see "mpls traffic-engineering diffserv-te te-class-map")

#.	Map class-type and tunnel priority to each TE class (see "mpls traffic-engineering diffserv-te te-class-map te-class")

To enter the DiffServ configuration hierarchy:


**Command syntax: diffserv-te**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)#

**Removing Configuration**

To revert all DiffServ configuration to the default values:
::

	dnRouter(cfg-protocols-mpls-te)# no diffserv-te


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+