traffic-engineering interface srlg-group
----------------------------------------

**Minimum user role:** operator

A shared risk link group (SRLG) is a set of links that share a common resource. The group members have a shared risk: when the common resource fails, all links in the group are equally affected and if one link fails other links in the group may also fail. 

In MPLS-TE, the SRLG feature ensures that a calculated backup path avoids using links that are in the same SRLG as interfaces that the backup tunnel is protecting.

A link may belong to multiple SRLGs. You can configure up to 32 SRLG groups on an interface. The SRLG attribute is shared between all TE enabled IGP protocols.
To configure an SRLG group for the MPLS-TE interface:


**Command syntax: srlg-group [srlg-id]**, [srlg-id], ..

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering interface

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle
	
	- Bundle vlan

**Parameter table**

+---------------+----------------------------------------------------------------------------------------+------------------+-------------+
|               |                                                                                        |                  |             |
| Parameter     | Description                                                                            | Range            | Default     |
+===============+========================================================================================+==================+=============+
|               |                                                                                        |                  |             |
| srlg-id       | The SRLG identifier. Links with the same SRLG   identifier belong to the same SRLG.    | 0..4294967295    | \-          |
+---------------+----------------------------------------------------------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1.1
	dnRouter(cfg-mpls-te-if)# srlg-group 1, 2
	dnRouter(cfg-mpls-te-if)# srlg-group 3
	
	
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1.2
	dnRouter(cfg-mpls-te-if)# srlg-group 3

**Removing Configuration**

To remove an SRLG value from the interface:
::

	dnRouter(cfg-mpls-te-if)# no srlg-group 1

To remove all SRLG values from the interface:
::

	dnRouter(cfg-mpls-te-if)# no srlg-group


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+