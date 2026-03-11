network-services vrf instance protocols bgp bestpath med
--------------------------------------------------------

**Minimum user role:** operator

The bestpath-med command instructs BGP what to do with the multi-exit discriminator (MED) metrics. By default, routes originating within the same confederation as the router do not have their MED values compared as part of the best-path selection process. Also BGP best-path selection considers a missing MED value to be 0, so routes with missing MED values will be preferred by default.

To change this behavior:

**Command syntax: bestpath med {confed, missing-as-worst}**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- These parameter options may be configured together or individually. When configured individually, the order is not important.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                      | Range   | Default |
+==================+==================================================================================+=========+=========+
| confed           | MEDs are compared for all paths that consist only of AS_CONFED_SEQUENCE. These   | Boolean | False   |
|                  | paths originated within the local confederation                                  |         |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+
| missing-as-worst | path received with no MED paths are assigned a MED of 4,294,967,294              | Boolean | False   |
+------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med confed

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med missing-as-worst

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath med confed missing-as-worst

    dnRouter(cfg-protocols-bgp)# bestpath med missing-as-worst confed


**Removing Configuration**

To disable the bestpath med configuration:
::

    dnRouter(cfg-protocols-bgp)# no bestpath med confed

::

    dnRouter(cfg-protocols-bgp)# no bestpath med missing-as-worst

::

    dnRouter(cfg-protocols-bgp)# no bestpath med

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
