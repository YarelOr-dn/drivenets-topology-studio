interfaces dhcp relay-agent source-interface
--------------------------------------------

**Minimum user role:** operator

"To set the source interface for the relay agent to relay IPv4 addresses:"

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent

**Note**

- The default behavior is to impose IPv4 source address matching of the ingress interface that received the DHCP messages.

- The IPv4 address must be configured for the selected interface.

- When the link-selection sub-option is in use the source-interface will be impose a GI address field.

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
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# source-interface lo0


**Removing Configuration**

To revert to default behavior:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
