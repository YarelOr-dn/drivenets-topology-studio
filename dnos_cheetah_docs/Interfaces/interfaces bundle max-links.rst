interfaces max-links
--------------------

**Minimum user role:** operator

Set the maximum number of interface members that can be active for the aggregate interface (bundle) at a given time.
Interface members are selected to be active according to their port-priority configuration.
An interface member not selected to be active in the aggregate interface will be in standby and will not pass traffic. In case an active member fails, a standby member will be used.
The max-link configuration is independent of LACP configuration.
If LACP is not enabled, the max-link configuration must be identical on both ends of the bundle link.
If LACP is enabled, the LACP state-machine takes precedence over the LAG selection mechanism.
To configure the maximum number of active links in the bundle interface:

**Command syntax: max-links [max-links]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to bundle interfaces.

- Max-links must be greater or equal to min-links. Commit validation expected

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| max-links | Set the maximum number of interface members that can be active for the aggregate | 1-64  | 64      |
|           | interface (bundle) at a given time. An interface member not selected to be       |       |         |
|           | active in the aggregate interface will be in standby and will not pass traffic   |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# max-links 1


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no max-links

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
