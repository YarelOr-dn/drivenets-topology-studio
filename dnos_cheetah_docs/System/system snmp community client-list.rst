system snmp community client-list
---------------------------------

**Minimum user role:** operator

A client-list is a group of clients that are provided with authorization to access the device. You can configure multiple client-lists for an SNMP community. By default an SNMP community has open access to all clients (0.0.0.0/0).

To configure a client-list:

**Command syntax: client-list [network-address]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

	- By default, snmp community has open access to all clients(0.0.0.0/0 or the IPv6 equivalent ::/0)

	- It is possible to configure multiple clients for an SNMP community per vrf

	- no command removes a specific / all clients for a given snmp community

**Parameter table**

+-------------+-------------------------------------------------------------------------------------------------+-----------+---------+
| Parameter   | Description                                                                                     | Range     | Default |
+=============+=================================================================================================+===========+=========+
| client-list | A group of clients to add to the SNMP community.                                                | A.B.C.D/x | \-      |
|             | You can configure multiple clients for an SNMP community.                                       | x:x::x:x  |         |
|             | By default an SNMP community has open access to all clients (0.0.0.0/0 or IPv6 equivalent ::/0) |           |         |
+-------------+-------------------------------------------------------------------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
	dnRouter(cfg-system-snmp-community)# client-list 192.168.0.0/24
	dnRouter(cfg-system-snmp-community)# client-list 172.17.0.0/16
	dnRouter(cfg-system-snmp-community)# client-list 2001:db8:2222::/48
	dnRouter(cfg-system-snmp-community)# client-list 2001:ab12::1/128
	


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-community)# no client-list
	dnRouter(cfg-system-snmp-community)# no client-list 172.17.0.0/16
	dnRouter(cfg-system-snmp-community)# no client-list 2001:db8:2222::/48

.. **Help line:** Configure system snmp community

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 5.1.0   | Command introduced                    |
+---------+---------------------------------------+
| 6.0     | Applied new hierarchy for SNMP        |
+---------+---------------------------------------+
| 9.0     | Applied new hierarchy for community   |
+---------+---------------------------------------+
| 15.1    | Added support for IPv6 address format |
+---------+---------------------------------------+


