interfaces revertive
--------------------

**Minimum user role:** operator

When a bundle is configured with max-links (N out of M), N ports are determined as active, the rest as standby.
If an active port is down, a standby port is selected instead.
You can set the revertive behavior for when higer port-priority member becomes available.
When enabled, when that higher port-priority link becomes operational or a link is added to the aggregated interface that is determined to be higher in priority, it takes precedence over a standby port currently active in the bundle.
To configure revertive behavior:

**Command syntax: revertive [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to bundle interfaces.

- If LACP is not enabled, the revertive configuration must be identical on both ends of the bundle link to prevent misaligned active ports.

**Parameter table**

+-------------+----------------------------------------------+--------------+----------+
| Parameter   | Description                                  | Range        | Default  |
+=============+==============================================+==============+==========+
| admin-state | The revertive state of the bundle interface. | | enabled    | disabled |
|             |                                              | | disabled   |          |
+-------------+----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# revertive enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no revertive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
