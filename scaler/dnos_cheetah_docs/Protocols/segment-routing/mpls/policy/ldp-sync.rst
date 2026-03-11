protocols segment-routing mpls policy ldp-sync
----------------------------------------------

**Minimum user role:** operator

When enabled, the SR-TE policy is excluded from the IGP shortcut calculations if an LDP peer of policy tail-end node is missing.


**Command syntax: ldp-sync [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Set ldp sync. If there is no ldp session to neighbor at policy tail-end, policy  | | enabled    | disabled |
|             | will be excluded from IGP                                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# ldp-sync enabeld


**Removing Configuration**

To revert the ldp-sync to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no ldp-sync

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
