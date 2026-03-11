interfaces dhcpv6 relay-agent source-interface
----------------------------------------------

**Minimum user role:** operator

"To set the source interface for the relay agent to relay IPv6 addresses:"

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- interfaces dhcpv6 relay-agent

**Note**

- The default behavior is to impose IPv6 source address matching of the ingress interface that received the DHCP messages.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| source-interface | The source-interface the relay agent uses as a source address to relay messages. | | string         | \-      |
|                  |                                                                                  | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcpv6 relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)# source-interface lo0


**Removing Configuration**

To revert to default behavior:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
