protocols ospf nsr
------------------

**Minimum user role:** operator

OSPF nonstop routing (NSR) enables an OSPF speaker to maintain OSPF adjacencies, state and database, while undergoing a switchover at the CPU level (e.g. NCC switchover). Unlike OSPF graceful-restart (GR), which requires support from an OSPF neighbor as GR helper, NSR recovery is transparent to the network and connected neighbors.
OSPF NSR is supported for cluster (external NCC) and stand-alone setups.
Configuration applies for all OSPFv2 instances in all VRFs.
To enable/disable OSPF NSR:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- NSR is mutually exclusive with GR support. OSPF NSR and OSPF graceful restart in restarting mode cannot be enabled at the same time.

**Parameter table**

+-----------+---------------------------+--------------+---------+
| Parameter | Description               | Range        | Default |
+===========+===========================+==============+=========+
| nsr       | Set OSPF Non Stop Routing | | enabled    | enabled |
|           |                           | | disabled   |         |
+-----------+---------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# nsr enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospf)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
