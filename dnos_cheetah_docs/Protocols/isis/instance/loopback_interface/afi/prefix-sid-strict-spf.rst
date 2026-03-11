protocols isis instance interface address-family prefix-sid strict-spf
----------------------------------------------------------------------

**Minimum user role:** operator

A prefix-SID is a type of a SID that is attached to an IP prefix. There are two types of Prefix-SID: Node-SID, which must be globally unique, and anycast-SID, which can be duplicated and can allow a type of very coarse traffic engineering. The node SID uses the node's loopback address as the prefix.

It is recommended to set the node-SID on the same loopback interface used for "routing-options router-id".

To allocate a prefix SID to a loopback interface address:

**Command syntax: prefix-sid strict-spf [sid-type] [sid-index/sid-label]** prefix-type [prefix-type] explicit-null

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**
- The command is applicable only to loopback interfaces.
- By default, the prefix-sid is assigned a node-sid.
- It is recommended that you set the Node-SID on the same loopback interface used for "routing-options router-id"
.. - Configured Prefix-SID will be compared with the configured SRGB value, if found out of block range (by either index or label), fail commit
.. - Configured Prefix-SID will be compared with the currently in used SRGB value, if found out of block range (by either index or label), SID will not be used and PREFIX_SID_OUT_OF_RANGE syslog will be sent after commit is applied
.. -  Cannot configure (commit validation) same sid-index or label for different prefix-sid. i.e for different algorithm prefix-sid or among different loopback interfaces

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
| Parameter           | Description                                                                      | Range                    | Default |
+=====================+==================================================================================+==========================+=========+
| sid-type            | Sid type absolute or index                                                       | | index                  | \-      |
|                     |                                                                                  | | label                  |         |
+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
| sid-index/sid-label | sid-index: Assigns the prefix-SID label according to the index of the            | | sid-index: 0-255999    | \-      |
|                     | Segment-Routing Global Block used by IS-IS. The value must be within the SRGB    | | sid-label: 16-955999   |         |
|                     | range.                                                                           |                          |         |
|                     | sid-label: Assigns the prefix-SID label as an absolute value. The value must be  |                          |         |
|                     | within the SRGB range.                                                           |                          |         |
+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
| prefix-type         | The type of SID for the router:                                                  | | node                   | node    |
|                     | node - The SID is used to identify the node in the network. The "node" type can  | | anycast                |         |
|                     | only be used for interfaces with an address of /32 (ipv4) or /128 (ipv6).        |                          |         |
|                     | anycast - This SID type may be identical on several routers, helping in creating |                          |         |
|                     | ECMP aware SFP paths                                                             |                          |         |
+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
| explicit-null       | When set, a penultimate hop neighbor of the Prefix-SID originator will replace   | Boolean                  | False   |
|                     | the Prefix-SID with a Prefix-SID that has an Explicit NULL value.                |                          |         |
|                     | When not used, the default behavior is implicit-null.                            |                          |         |
+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid index 1

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid label 16001 explicit-null

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo1
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid index 3000 prefix-type anycast

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid index 22 algorithm spf
    dnRouter(cfg-inst-if-afi)# prefix-sid strict-spf index 23


**Removing Configuration**

dnRouter(cfg-inst-if-afi)# no prefix-sid strict-spf
::

    dnRouter(cfg-inst-if-afi)# no prefix-sid strict-spf index 22

**Command History**

+---------+------------------------------------------------+
| Release | Modification                                   |
+=========+================================================+
| 14.0    | Command introduced                             |
+---------+------------------------------------------------+
| 15.0    | Added support for spf and strict-spf algorithm |
+---------+------------------------------------------------+
