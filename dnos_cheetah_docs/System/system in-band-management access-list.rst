system in-band-management access-list
-------------------------------------

**Minimum user role:** operator

The control-plane access-list is supported only on in-band traffic and is hardware-configured to allow or block different IPv4/IPv6 traffic destined to the NCC (i.e. to any local address, including multicast packets).

To apply an access-list to the control plane traffic designated to a local address:

**Command syntax: access-list [access-list-type] [access-list-name]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- The access-list will not affect transit traffic.

.. - no command removes a specific access-list, or all access-lists in a specific type

**Parameter table**

+------------------+------------------------------------------------------------+-------------------------------------+---------+
| Parameter        | Description                                                | Range                               | Default |
+==================+============================================================+=====================================+=========+
| access-list-type | Filter the displayed information to a specific type        | IPv4                                | \-      |
|                  |                                                            | IPv6                                |         |
+------------------+------------------------------------------------------------+-------------------------------------+---------+
| access-list-name | Filter the displayed information to a specific access-list | The name of an existing access-list | \-      |
+------------------+------------------------------------------------------------+-------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# in-band-management access-list ipv4 IPv4_CP_ACL
	dnRouter(cfg-system)# in-band-management access-list ipv6 IPv6_CP_ACL




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system)# no in-band-management access-list
	dnRouter(cfg-system)# no in-band-management access-list ipv4
	dnRouter(cfg-system)# no in-band-management access-list ipv6

.. **Help line:** configure control plane access list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
