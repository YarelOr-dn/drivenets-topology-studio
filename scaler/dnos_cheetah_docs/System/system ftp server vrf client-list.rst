system ftp server vrf client-list
---------------------------------

**Minimum user role:** operator

Use the following command to configure the black or white list of incoming IP addresses per VRF for ftp server:

**Command syntax: server vrf client-list [ipv4-address/ipv6-address]**

**Command mode:** config

**Hierarchies**

- system ftp server vrf


**Note**

- If the client-list type is set to 'allow', the client-list must not be empty.

- Supports up to 1000 clients (for both addresses together)

- The 'no client-list ' without a value removes all ip addresses from the list.

- The 'no client-list ' with a value removes the specified ip address from the list.

.. - no command without value removes all the IP addresses from the list.

	- no command with value removes the specified IP addresses from the list.

	Scale validation:

	-  up to 1000 clients (for both of addresses together) per vrf

	-  if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+------------+---------------------------------------------------------------------------------------------------+----------------+---------+
| Parameter  | Description                                                                                       | Range          | Default |
+============+===================================================================================================+================+=========+
| ip-address | Configure incoming IP addresses that will or will not be permitted access to FTP server sessions. | A.B.C.D/x      | \-      |
|            |                                                                                                   | xx:xx::xx:xx/x |         |
+------------+---------------------------------------------------------------------------------------------------+----------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)# client-list 200.10.10.6/32
	dnRouter(cfg-system-ftp-server)# client-list 2001:ab12::1/128
	dnRouter(cfg-system-ftp-server)# client-list 50.1.22.0/24
	dnRouter(cfg-system-ftp-server)# client-list 2001:db8:2222::/48





**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no client-list 2001:ab12::1/128
	dnRouter(cfg-system-ftp-server)# no client-list

.. **Help line:** configure black or white list of incoming IP-addresses per VRF for ftp server.

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 11.6    | Command introduced                    |
+---------+---------------------------------------+
| 13.1    | Moved the command under VRF hierarchy |
+---------+---------------------------------------+
