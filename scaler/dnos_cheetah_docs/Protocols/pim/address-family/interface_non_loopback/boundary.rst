protocols pim address-family interface boundary
-----------------------------------------------

**Minimum user role:** operator

Setting an IP multicast boundary policy controls the IP multicast forwarding for a predefined multicast group range. The boundary policy applies to the interface under which it is defined.

To configure an IP multicast boundary policy on an interface:

**Command syntax: boundary [boundary-policy-prefix-list]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family interface

**Note**
- The default boundary policy is 'allow' for all group ranges.

**Parameter table**

+-----------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter                   | Description                                                                      | Range            | Default |
+=============================+==================================================================================+==================+=========+
| boundary-policy-prefix-list | The prefix-list name which uniquely identify a boundary policy that contains one | | string         | \-      |
|                             | or more policy rules used to accept or reject certain multicast groups. If a     | | length 1-255   |         |
|                             | policy is not specified, PIM join with all group addresses are accepted.         |                  |         |
+-----------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface ge100-1/2/1
    dnRouter(cfg-protocols-pim-af4-if)# boundary BOUNDARY_LOCAL_MC_POL


**Removing Configuration**

To delete the boundary policy:
::

    dnRouter(cfg-protocols-pim-af4-if)# no boundary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
