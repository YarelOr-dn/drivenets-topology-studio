system dns server priority ip-address
-------------------------------------

**Minimum user role:** operator

Domain name system (DNS) servers are used for resolving host-names to IP addresses. You can configure up to three DNS servers that the system can contact to resolve a host-name per VRF per system.

**Command syntax: server priority [priority] ip-address [ip-address]**

**Command mode:** config

**Hierarchies**

- system dns

**Note**
- DNS servers that are acquired through DHCP are not subject to the configured priority.

- When mgmt0 interface are configured to DHCP mode, the configured list of DNS servers is not applied to the system. Instead, the DNS servers' list is acquired by the DHCP client.

	  - Up to 3 DNS servers can be configured per vrf, in-band (vrf default and non-default-vrf) and out-of-band (vrf mgmt0).

        -  validation: is required to fail commit if more than 3 non-default VRFs are configured in general

	  - DNS servers acquired from DHCP server are not subjected to the configured priority

	  - vrf "default" represents the in-band management dns server, while vrf "mgmt0" represents the out-of-band management dns servers.

	  - When mgmt0 interface are configured to DHCP mode, configured list of DNS servers is not applied to the system. Instead, DNS servers list is acquired by DHCP client.

	  - DNS servers acquired from DHCP server are not subjected to the configured priority

	  - DNS quarries will be resolved in the same VRF they where issued, in case there in no DNS server configured, quarries will be dropped.

**Parameter table**

+------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                                      | Range        | Default |
+============+==================================================================================+==============+=========+
| priority   | The priority is used for the order in which the DNS servers are contacted until  | 1-255        | \-      |
|            | the host-name is resolved.                                                       |              |         |
|            | Priority 1 is the highest priority. You can only configure one priority per      |              |         |
|            | server.                                                                          |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+
| ip-address | The address of the DNS server, can be either IPv4 or IPv6.                       | | A.B.C.D    | \-      |
|            |                                                                                  | | X:X::X:X   |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# server priority 1 ip-address 12.127.17.83
    dnRouter(cfg-system-dns)# server priority 7 ip-address 12.127.16.83
    dnRouter(cfg-system-dns)# server priority 3 ip-address 12.33.16.22
    dnRouter(cfg-system-dns)# server priority 40 ip-address 9876:65::1


**Removing Configuration**

To delete the DNS server configuration:
::

    dnRouter(cfg-system-dns)# no server priority 1

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                             |
+=========+==========================================================================================================================+
| 11.4    | Command introduced                                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 13.1    | Command from the "system out-of-band" hierarchy merged with the "system dns" hierarchy by adding VRF to the syntax       |
|         | (default for in-band; mgmt0 for out-of-band)                                                                             |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 15.0    | Updated priority range                                                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for IPv6 address format and changed the priority range from maximum 6 to 255                               |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Removed mgmt-ncc-x interfaces                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 19.1    | Added non default VRF support                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------+
