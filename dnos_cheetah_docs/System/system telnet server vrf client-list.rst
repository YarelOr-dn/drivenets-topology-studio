system telnet server vrf client-list
------------------------------------

**Minimum user role:** operator

To configure a list of IP addresses that will or will not be permitted access to Telnet server sessions (black or white list):

**Command syntax: server vrf client-list [ipv4-address/ipv6-address]**

**Command mode:** config

**Hierarchies**

- system telnet server vrf

**Note**

- A client-list configured under VRF mgmt0 will be implicitly attached and applied on the host out-of-band interfaces (mgmt-ncc-0 and mgmt-ncc-1).

.. - no command without value removes all the IP addresses from the list.

	- no command with value removes the specified IP addresses from the list.

	Scale validation:

	- up to 1000 clients (for both of addresses together) per vrf

	- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+------------+------------------------------------------------------------------------------------------------------+----------------+---------+
| Parameter  | Description                                                                                          | Range          | Default |
+============+======================================================================================================+================+=========+
| IP-address | Configure incoming IP addresses that will or will not be permitted access to Telnet server sessions. | A.B.C.D/x      | \-      |
|            |                                                                                                      | xx:xx::xx:xx/x |         |
+------------+------------------------------------------------------------------------------------------------------+----------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# server vrf default
	dnRouter(cfg-telnet-server-vrf)# client-list 200.10.10.6/32
	dnRouter(cfg-telnet-server-vrf)# client-list 2001:ab12::1/128
	dnRouter(cfg-telnet-server-vrf)# client-list 50.1.22.0/24
	dnRouter(cfg-telnet-server-vrf)# client-list 2001:db8:2222::/48
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-telnet-server-vrf)# no client-list 2001:ab12::1/128
	dnRouter(cfg-telnet-server-vrf)# no client-list

.. **Help line:** configure black or white list of incoming IP-addresses per vrf for telnet server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

