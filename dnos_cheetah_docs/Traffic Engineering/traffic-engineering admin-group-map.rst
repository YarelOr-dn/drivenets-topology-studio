traffic-engineering admin-group-map
-----------------------------------

**Minimum user role:** operator

RSVP allows you to configure administrative groups for CSPF path selection. Administrative groups allow you to group links with similar characteristics. An administrative group is typically:

-	Named with a color (see "mpls traffic-engineering admin-group-map bit-position")

-	Assigned a numeric value (see "mpls traffic-engineering admin-group-map bit-position"). Lower numbers indicate higher priority.

-	 Applied to an RSVP interface for the appropriate link (see "mpls traffic-engineering interface admin-group")

Once admin-groups are created, you can use them to include or exclude links in RSVP tunnels. See how in "rsvp tunnel primary admin-group include" and "rsvp tunnel primary admin-group exclude".

To create an admin-group, enter the admin-group-map configuration mode:

**Command syntax: admin-group-map**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# admin-group-map
	dnRouter(cfg-mpls-te-admin-group-map)#

**Removing Configuration**

To remove all admin-group configuration:
::

	dnRouter(cfg-protocols-mpls-te)# no admin-group-map 


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+