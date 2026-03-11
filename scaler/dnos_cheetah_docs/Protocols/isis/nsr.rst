protocols isis nsr
------------------

**Minimum user role:** operator

IS-IS nonstop routing (NSR) enables an IS-IS speaker to maintain IS-IS adjacencies, state and database, while undergoing a switchover at the CPU level (e.g. NCC switchover).
Unlike IS-IS graceful-restart (GR), which requires support from an IS-IS neighbor as GR helper, NSR recovery is transparent to the network and connected neighbors.

IS-IS NSR is supported for cluster (external NCC) and stand-alone setups.

To enable/disable isis NSR:

**Command syntax: nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- NSR is mutually exclusive with GR support. IS-IS nsr and IS-IS graceful restart cannot be enabled at the same time.

**Parameter table**

+-----------+----------------------------+--------------+---------+
| Parameter | Description                | Range        | Default |
+===========+============================+==============+=========+
| nsr       | Set IS-IS Non Stop Routing | | enabled    | enabled |
|           |                            | | disabled   |         |
+-----------+----------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# nsr enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
