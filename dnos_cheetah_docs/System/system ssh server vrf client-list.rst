system ssh server vrf client-list
---------------------------------

**Minimum user role:** operator

The IP-addresses per vrf for SSH server

**Command syntax: client-list [ipv4-address/ipv6-address]** [, ipv4-address/ipv6-address, ipv4-address/ipv6-address]

**Command mode:** config

**Hierarchies**

- system ssh server vrf

**Note**

- no command without value removes all the IP addresses from the list.

- no command with value removes the specified IP addresses from the list.

- Scale validation

- up to 1000 clients (for both of addresses together) per vrf

- if client-list type is set to "allow", client-list must not be empty.

**Parameter table**

+---------------------------+------------------------------------------------------------------------+----------------+---------+
| Parameter                 | Description                                                            | Range          | Default |
+===========================+========================================================================+================+=========+
| ipv4-address/ipv6-address | Black/white list of incoming ip-prefixes for system in-band ssh server | | A.B.C.D/x    | \-      |
|                           |                                                                        | | X:X::X:X/x   |         |
+---------------------------+------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-ssh)# server vrf default
    dnRouter(cfg-ssh-server-vrf)# client-list 200.10.10.6/32
    dnRouter(cfg-ssh-server-vrf)# client-list 2001:ab12::1/128
    dnRouter(cfg-ssh-server-vrf)# client-list 50.1.22.0/24
    dnRouter(cfg-ssh-server-vrf)# client-list 2001:db8:2222::/48


**Removing Configuration**

To remove the a specific from the list:
::

    dnRouter(cfg-ssh-server-vrf)# no client-list 2001:ab12::1/128

To remove all addresses from the list:
::

    dnRouter(cfg-ssh-server-vrf)# no client-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
