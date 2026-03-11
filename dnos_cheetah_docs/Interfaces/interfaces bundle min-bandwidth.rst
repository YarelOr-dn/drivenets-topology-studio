interfaces min-bandwidth
------------------------

**Minimum user role:** operator

You can set the minimum bandwidth required for the bundle interface to be available (operational status "up"). This option is particularly useful if you have a bundle interface with two links (e.g. one 400Gbps link and another 100Gbps link). The total bandwidth of the bundle interface in this example is 500Gbps, but min-links may not be enough.

If min-links is configured, both configurations apply. That is, if min-links is set to 2 and min-bandwidth is set to 100Gbps, then the operational status of the bundle interface in the above example will be "down" if the 100Gbps link goes down, even though the minimum bandwidth condition is met.

The min-bandwidth configuration is independent of LACP configuration. If LACP is not enabled, the min-bandwidth configuration must be identical on both ends of the bundle link. If LACP is enabled, the LACP state-machine takes precedence over the LAG selection mechanism.

To configure the minimum bandwidth for an aggregated Ethernet bundle:

**Command syntax: min-bandwidth [min-bandwidth]** [units]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to bundle interfaces.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter     | Description                                                                      | Range        | Default |
+===============+==================================================================================+==============+=========+
| min-bandwidth | The minimum bandwidth for the aggregated bundle interface. 0 means no bandwidth  | 0-6400000000 | 0       |
|               | restriction on the bundle; min-bandwidth will never be triggered.                |              |         |
+---------------+----------------------------------------------------------------------------------+--------------+---------+
| units         | The units used for bandwidth. If you do not specify the unit, kbps will be used. | | kbps       | kbps    |
|               |                                                                                  | | mbps       |         |
|               |                                                                                  | | gbps       |         |
+---------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# min-bandwidth 10000 mbps
    dnRouter(cfg-if-bundle-1)# min-bandwidth 1200000 kbps
    dnRouter(cfg-if-bundle-1)# min-bandwidth 1234567890


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no min-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
