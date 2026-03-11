protocols msdp mesh-group policy in
-----------------------------------

**Minimum user role:** operator

Use the command to set the MSDP SA filter "IN" policy for the MSDP mesh-group. The 'group-prefix-list' defines the allowed/denied filter for SA Group addresses. The 'rps-prefix-list' defines the allowed/denied RP addresses.

**Command syntax: policy in {rps [source-rps-prefix-list], group [group-prefix-list]}**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group

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
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# policy in group SA-FILTER-IN-Prefix-List

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# policy in rps RPS-FILTER-IN-Prefix-List


**Removing Configuration**

To clear the SA in RP/Group filtering policies:
::

    dnRouter(cfg-protocols-msdp-group)# no policy in

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
