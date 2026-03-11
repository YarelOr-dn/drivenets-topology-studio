protocols isis instance address-family ipv4-unicast ti-fast-reroute maximum-labels
----------------------------------------------------------------------------------

**Minimum user role:** operator

Sets the maximum allowed number of labels on the TI-LFA constructed label stack. 
If the calculated path exceeds the allowed maximum then an LFA path will not be provided by IS-IS and no alternate path will be installed.  
To set the maximum-labels:

**Command syntax: maximum-labels [maximum-labels]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast ti-fast-reroute

**Note**

- If the level is not specified, it will be set for all isis supported levels.

- Level-1-2 settings will be the default of per-level behavior.

**Parameter table**

+----------------+-----------------------------+-------+---------+
| Parameter      | Description                 | Range | Default |
+================+=============================+=======+=========+
| maximum-labels | configuration for level-1-2 | 1-5   | 3       |
+----------------+-----------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# maximum-labels 2
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# maximum-labels 4


**Removing Configuration**

To revert the maximum-labels to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no maximum-labels

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
