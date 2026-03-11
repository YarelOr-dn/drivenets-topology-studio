protocols ospf instance area interface prefix-sid strict-spf
------------------------------------------------------------

**Minimum user role:** operator

A prefix-SID is a type of a SID that is attached to an IP prefix. There are two types of Prefix-SIDs: Node-SID, which must be globally unique, and anycast-SID, which can be duplicated and can allow a type of very coarse traffic engineering.
The node SID uses the node's loopback address as the prefix.
It is recommended to set the node-SID on the same loopback interface used for "routing-options router-id".
When choosing strict-spf, the SID will be advertised with a strict-spf algorithm, enforcing all nodes to utilize a unicast spf forwarding solution when designating traffic towards the SID.
To allocate a prefix SID to a loopback interface address:

**Command syntax: prefix-sid strict-spf [sid-type] [sid-index]** prefix-type [prefix-sid-type] explicit-null

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- The command is applicable only to loopback interfaces

- By default, the prefix-sid is assigned a node-sid

- It is recommended that you set the Node-SID on the same loopback interface used for "routing-options router-id"

- Configured Prefix-SID will be compared with the configured SRGB value. If found out of block range (by either index or label), the commit will fail

- Configured Prefix-SID will be compared with the currently in used SRGB value. If found out of block range (by either index or label), the SID will not be used and PREFIX_SID_OUT_OF_RANGE syslog will be sent after the commit is applied

- Cannot configure (commit validation) same sid-index or label for different prefix-sids, i.e for different algorithm prefix-sid or among different loopback interfaces.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter       | Description                                                                      | Range        | Default |
+=================+==================================================================================+==============+=========+
| sid-type        | Sid type absolute or index                                                       | | index      | \-      |
|                 |                                                                                  | | absolute   |         |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| sid-index       | Sid value                                                                        | 0-1040383    | \-      |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| prefix-sid-type | Prefix Sid type                                                                  | | node       | node    |
|                 |                                                                                  | | anycast    |         |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| explicit-null   | When set, the penultimate hop must swap the prefix SID for the relevant explicit | Boolean      | False   |
|                 | null label before forwarding the packet.                                         |              |         |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface lo0
    dnRouter(cfg-ospf-area-interface)# prefix-sid strict-spf index 1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface lo0
    dnRouter(cfg-ospf-area-interface)# prefix-sid strict-spf label 16001 explicit-null

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface lo0
    dnRouter(cfg-ospf-area-interface)# prefix-sid strict-spf index 3000 prefix-type anycast


**Removing Configuration**

To remove the prefix-sid settings:
::

    dnRouter(cfg-ospf-area-interface)# no prefix-sid strict-spf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
