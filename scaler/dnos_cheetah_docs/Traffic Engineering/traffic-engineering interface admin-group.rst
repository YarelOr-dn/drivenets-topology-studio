traffic-engineering interface admin-group
-----------------------------------------

**Minimum user role:** operator

You can set multiple admin-groups on an interface to enable multiple RSVP tunnels to pass through the interface.

To set the admin-group on an interface:


**Command syntax: admin-group [admin-group-name]**, [admin-group-name], .

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering interface

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle
	
	- Bundle vlan

- Changing an admin-interface only affects new tunnels.

**Parameter table**

+---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                 |                      |             |
| Parameter           | Description                                                                                                                                                     | Range                | Default     |
+=====================+=================================================================================================================================================================+======================+=============+
|                     |                                                                                                                                                                 |                      |             |
| admin-group-name    | Specify an existing admin-group name (or multiple   admin-group names) to associate with the interface. You can set up to 32   admin-groups on an interface.    | 1..255 characters    | \-          |
+---------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1
	dnRouter(cfg-mpls-te-if)# admin-group AFF_1
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# interface bundle-2
	dnRouter(cfg-mpls-te-if)# admin-group AFF_1, AFF_2

**Removing Configuration**

To remove all admin-groups on the interface:
::

	dnRouter(cfg-mpls-te-if)# no admin-group 

To remove an admin-group on the interface: 
::

	dnRouter(cfg-mpls-te-if)# no admin-group AFF_2

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+