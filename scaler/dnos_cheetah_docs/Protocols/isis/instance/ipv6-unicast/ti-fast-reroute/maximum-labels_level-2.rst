protocols isis instance address-family ipv6-unicast ti-fast-reroute maximum-labels level level-2
------------------------------------------------------------------------------------------------

**Minimum user role:** operator

Sets the maximum allowed number of labels on the TI-LFA constructed label stack. 
If the calculated path exceeds the allowed maximum then an LFA path will not be provided by IS-IS and no alternate path will be installed.
To set the maximum-labels:

**Command syntax: maximum-labels level level-2 [maximum-labels]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast ti-fast-reroute

**Parameter table**

+----------------+---------------------------+-------+---------+
| Parameter      | Description               | Range | Default |
+================+===========================+=======+=========+
| maximum-labels | configuration for level-2 | 1-5   | \-      |
+----------------+---------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# maximum-labels level level-2 2
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# maximum-labels level level-2 4


**Removing Configuration**

To revert the maximum-labels to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no maximum-labels level level-2 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
