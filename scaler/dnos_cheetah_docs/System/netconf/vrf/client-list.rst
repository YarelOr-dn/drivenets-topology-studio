system netconf vrf client-list
------------------------------

**Minimum user role:** operator

Create a list of clients that are permitted or denied to open netconf sessions to the system (according to \"system netconf vrf client-list type\".

To configure a client-list:

**Command syntax: client-list [ipv4-address/ipv6-address]** [, ipv4-address/ipv6-address, ipv4-address/ipv6-address]

**Command mode:** config

**Hierarchies**

- system netconf vrf

**Note**

- You can add up to 10 clients (for both IPv4 and IPv6 addresses combined) per VRF.

**Parameter table**

+---------------------------+-------------------------------------------------------------------+--------------+---------+
| Parameter                 | Description                                                       | Range        | Default |
+===========================+===================================================================+==============+=========+
| ipv4-address/ipv6-address | White list of incoming IPv4/IPv6 addresses of the NETCONF clients | A.B.C.D/x    | \-      |
|                           |                                                                   | X:X::X:X/x   |         |
+---------------------------+-------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf vrf default
    dnRouter(cfg-system-netconf-vrf)# client-list 100.54.12.1/32
    dnRouter(cfg-system-netconf-vrf)# client-list 210.4.21.0/24
    dnRouter(cfg-system-netconf-vrf)# client-list 2001:db8:2222::/48


**Removing Configuration**

To remove a specific client from the client list:
::

    dnRouter(cfg-system-netconf-vrf)# no client-list 100.54.12.1/32

To remove all clients from the client-list:
::

    dnRouter(cfg-system-netconf-vrf)# no client-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
