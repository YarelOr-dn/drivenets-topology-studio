protocols pim address-family mofrr protected-groups
---------------------------------------------------

**Minimum user role:** operator

The MoFRR protected-groups is a prefix list that defines the group ranges to be protected. The command enables MoFRR on all new and existing (S,G) PIM states within the protected group.

To configure MoFRR protected-groups prefix list:

**Command syntax: protected-groups [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family mofrr

**Note**
- The default MoFRR protected group range is an empty group.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| prefix-list-name | MoFRR protected groups addresses. The prefix-list name which specifies the group | | string         | \-      |
|                  | addresses G's, which any (S,G) PIM state with these Group addresses will be      | | length 1-255   |         |
|                  | MoFRR protected by PIM.                                                          |                  |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)# protected-groups MOFRR_PROTECTED_GROUPS


**Removing Configuration**

To clear a specific set of protected groups and disable MoFRR on existing (S,G) PIM entries:
::

    dnRouter(cfg-pim-address-family-mofrr)# no protected-groups MOFRR_PROTECTED_GROUPS

To clear all protected groups and disable MoFRR on existing (S,G) PIM entries:
::

    dnRouter(cfg-pim-address-family-mofrr)# no protected-groups

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
