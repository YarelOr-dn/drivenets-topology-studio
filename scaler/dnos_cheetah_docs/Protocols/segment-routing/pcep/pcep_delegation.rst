protocols segment-routing pcep delegation
-----------------------------------------

**Minimum user role:** operator

Enables delegating SR-TE to a remote PCE.
For a delegated policy, the local router (acting as a PCC) will comply with policy updates provided by the PCE.
A policy path provided by the PCE will be considered as the most preferred path.
Policy information is passed to the PCE even if it is not delegated to it.

To enable delegating SR-TE:

**Command syntax: delegation [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------+----------+
| Parameter   | Description                                                                      | Range      | Default  |
+=============+==================================================================================+============+==========+
| admin-state | Enable SR-TE policy delegation to a remote PCE. Configuration apply as default   | enabled    | disabled |
|             | behavior for any sr-te policy                                                    | disabled   |          |
+-------------+----------------------------------------------------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# delegation enabeld


**Removing Configuration**

To revert the pcep delegation to its default value:
::

    dnRouter(cfg-protocols-sr-pcep)# no delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
