protocols isis instance interface address-family prefix-sid flex-algo
---------------------------------------------------------------------

**Minimum user role:** operator

A prefix-SID is a type of a SID that is attached to an IP prefix.
There are two types of Prefix-SID: A Node-SID, which must be globally unique, and an Anycast-SID, which can be duplicated and can allow a type of very coarse traffic engineering.
The node SID uses the node's loopback address as the prefix.
Assigning a prefix-sid Flex-Algo, will allow prefix-sid reachability only in the assigned Flex-Algo id domain. It is recommended to set the node-SID on the same loopback interface used for "routing-options router-id".

To allocate a prefix SID Flex-Algo to a loopback interface address:

**Command syntax: prefix-sid flex-algo [flex-algo id] [sid-type] [sid-index/sid-label]** prefix-type [prefix-type] explicit-null

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**
- The command is applicable only to loopback interfaces.
- By default, the prefix-sid is assigned a Node-Sid.
- Can set multiple prefix-sids of different Flex-Algo identifiers for the same loopback interface. All sids must have different local labels.
- It is recommended that you set the Node-SID on the same loopback interface used for "routing-options router-id".
.. - The configured Prefix-SID will be compared with the configured SRGB value, if found out of block range (by either index or label), the commit will fail.
.. - The configured Prefix-SID will be compared with the currently in used SRGB value, if found out of block range (by either index or label), the SID will not be used and the PREFIX_SID_OUT_OF_RANGE syslog will be sent after the commit is applied.
.. -  Cannot configure (commit validation) the same sid-index or label for different prefix-sids. i.e for different algorithm prefix-sid or among different loopback interfaces.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
| Parameter           | Description                                                                      | Range                    | Default |
+=====================+==================================================================================+==========================+=========+
| flex-algo id        | flex algorithm identifier                                                        | 128-255                  | \-      |
+---------------------+----------------------------------------------------------------------------------+--------------------------+---------+
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
    dnRouter(cfg-inst-if-afi)# prefix-sid flex-algo 128 index 1

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv6-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid flex-algo 128 index 100

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid flex-algo 128 label 16001 explicit-null

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo1
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# prefix-sid flex-algo 128 index 3000 prefix-type anycast


**Removing Configuration**

To revert prefix-sid optional to its default value:
::

    dnRouter(cfg-inst-if-afi)# no prefix-sid flex-algo 128 index 1 explicit-null

To remove a prefix-sid of a specific flex-algo
::

    dnRouter(cfg-inst-if-afi)# no prefix-sid flex-algo 128

To remove all flex-algo prefix-sids
::

    dnRouter(cfg-inst-if-afi)# no prefix-sid flex-algo

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 18.0    | Command introduced                                   |
+---------+------------------------------------------------------+
| 18.1    | Add support for flex-algo prefix-sid in ipv6-unicast |
+---------+------------------------------------------------------+
