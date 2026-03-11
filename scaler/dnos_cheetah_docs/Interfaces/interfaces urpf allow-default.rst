interfaces urpf allow-default
-----------------------------

**Minimum user role:** operator

Set whether to allow a match on default route for uRPF validity check. When disabled, the default route is excluded from the uRPF validity check. If the source IP forwarding table lookup results in a match upon default route, the packet will be dropped by uRPF. When enabled, the default route is included in the uRPF validity check.

To enable/disable uRPF for the default route:

**Command syntax: allow-default [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces urpf

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - IRB

- allow-default configuration must be identical for all urpf-enabled interfaces.

- In uRPF loose mode - the default route can point to any interface.

- If the Source IP matches to next-hop null0, the packet will be dropped.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Set the administrative state of the uRPF validity check for default route        | | enabled    | disabled |
|             | matching.                                                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# urpf
    dnRouter(cfg-if-bundle-1-urpf)# allow-default enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1-urpf)# no allow-default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
