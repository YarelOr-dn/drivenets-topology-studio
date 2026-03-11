protocols msdp default-peer policy out
--------------------------------------

**Minimum user role:** operator

Use the command to set the MSDP SA filter "OUT" policy for the MSDP default policy. The 'group-prefix-list' defines the allowed/denied filter for SA Group addresses. The 'rps-prefix-list' defines the allowed/denied RP addresses.

**Command syntax: policy out {rps [source-rps-prefix-list], group [group-prefix-list]}**

**Command mode:** config

**Hierarchies**

- protocols msdp default-peer

**Note**
- The 'group-prefix-list' defines the allowed/denied filter for SA Group addresses.

- The 'rps-prefix-list' defines the allowed/denied RP addresses.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter              | Description                                                                      | Range            | Default |
+========================+==================================================================================+==================+=========+
| source-rps-prefix-list | The prefix-list name which uniquely identify the SA source RP IPv4 address SA    | | string         | \-      |
|                        | filter policy that contains one or more policy rules used to accept or reject    | | length 1-255   |         |
|                        | MSDP SA from certain Source RP IP addresses. If a policy is not specified, MSDP  |                  |         |
|                        | SA from all RP sources are accepted.                                             |                  |         |
+------------------------+----------------------------------------------------------------------------------+------------------+---------+
| group-prefix-list      | The prefix-list name which uniquely identify a group address SA filter policy    | | string         | \-      |
|                        | that contains one or more policy rules used to accept or reject MSDP SA with     | | length 1-255   |         |
|                        | certain multicast groups. If a policy is not specified, MSDP SA with all group   |                  |         |
|                        | addresses are accepted.                                                          |                  |         |
+------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# policy out group SA-FILTER-OUT-Prefix-List

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# policy out rps RPS-FILTER-OUT-Prefix-List


**Removing Configuration**

To clear all SA out filtering policies:
::

    dnRouter(cfg-protocols-msdp-default-peer)# no policy out

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
