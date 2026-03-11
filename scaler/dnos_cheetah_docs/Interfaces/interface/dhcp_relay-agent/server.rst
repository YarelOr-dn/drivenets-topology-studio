interfaces dhcp relay-agent server
----------------------------------

**Minimum user role:** operator

To configure target DHCP servers for the relay agent:

**Command syntax: server [ip-address]** [, ip-address, ip-address]

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent

**Note**

- Up to 8 DHCP servers may be configured for a relay agent

- The DHCP servers must be in the same VRF as the relaying interface

**Parameter table**

+------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                                      | Range   | Default |
+============+==================================================================================+=========+=========+
| ip-address | List of IPv4 addresses of DHCP servers to which the relay agent should forward   | A.B.C.D | \-      |
|            | DHCPv4 requests. The relay agent is expected to forward DHCPv4/BOOTP requests to |         |         |
|            | all listed server addresses when DHCPv4 relaying is enabled globally, or on the  |         |         |
|            | interface                                                                        |         |         |
+------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# server 10.10.10.10, 20.20.20.20


**Removing Configuration**

To remove all DHCP servers from the list:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no server

To remove a specific DHCP server from the list:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no server 10.10.10.10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
