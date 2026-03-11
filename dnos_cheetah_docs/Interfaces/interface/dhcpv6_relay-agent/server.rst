interfaces dhcpv6 relay-agent server
------------------------------------

**Minimum user role:** operator

To configure a target DHCP IPv6 server for the relay agent:

**Command syntax: server [ipv6-address]** [, ipv6-address, ipv6-address]

**Command mode:** config

**Hierarchies**

- interfaces dhcpv6 relay-agent

**Note**

- Up to 2 DHCP servers may be configured for a relay agent.

- The DHCP servers must be in the same VRF as the relaying interface.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| ipv6-address | List of IPv6 addresses of DHCP servers to which the relay agent should forward   | X:X::X:X | \-      |
|              | DHCPv6 requests. The relay agent is expected to forward DHCPv6/BOOTP requests to |          |         |
|              | all listed server addresses when DHCPv6 relaying is enabled globally, or on the  |          |         |
|              | interface                                                                        |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcpv6 relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)# server faba:bb00::10:10:10:10


**Removing Configuration**

To remove all DHCP servers from the list:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no server

To remove a specific DHCP server from the list:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no server faba:bb00::10:10:10:10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
