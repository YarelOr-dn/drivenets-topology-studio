protocols isis instance address-family ipv4-unicast ti-fast-reroute protection-mode level level-2
-------------------------------------------------------------------------------------------------

**Minimum user role:** operator

Sets the required ti-fast-reroute protection for a given ISIS afi and level.
Configuring Shared Risk Link Group (SRLG) protection in TI-LFA Fast-reroute for segment routing allows for a fast reroute backup path that shares no common SRLG with the protected (primary) path.
Links with the same SRLG configuration typically share a common fiber, meaning they may fail if the fiber breaks. TI-LFA SRLG-disjoint protection attempts to find a backup path that excludes the SRLG of the protected path All links of the protected path that share any SRLG with the candidate backup paths are excluded.
For link protection, only the link protection LFA will be calculated. If none are found, no LFA will be provided.
For node protection, first find the node protecting the LFA paths. If none are found, a link protection LFA path will be calculated.

SRLG-disjoint - once set, the fast-reroute LFA path will be an SRLG disjoint with a primary path egress interface SRLG value.

To set the ti-fast-reroute protection:

**Command syntax: protection-mode level level-2 [protection-mode]** srlg-disjoint

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast ti-fast-reroute

**Note**

- Node protection calculation has a higher calculation complexity, and may risk that ISIS will find an LFA path in the required time.

**Parameter table**

+-----------------+-------------------------------------------+----------+---------+
| Parameter       | Description                               | Range    | Default |
+=================+===========================================+==========+=========+
| protection-mode | configuration for level-2                 | | link   | \-      |
|                 |                                           | | node   |         |
+-----------------+-------------------------------------------+----------+---------+
| srlg-disjoint   | srlg-disjoint configuration for level-1-2 | \-       | \-      |
+-----------------+-------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# protection-mode level level-2 node
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# protection-mode level level-2 link
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# protection-mode level level-2 node srlg-disjoint


**Removing Configuration**

To revert the protection-mode to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no protection-mode level level-2 

To revert the srlg-disjoint constraint:
::

    dnRouter(cfg-inst-afi-ti-frr)# no protection-mode level level-2 node srlg-disjoint

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
| 18.1    | Command introduced |
+---------+--------------------+
