services mpls-oam profile probe-loss consecutive-threshold
----------------------------------------------------------

**Minimum user role:** operator


Probes are sent periodically, at a rate of count x interval, where count is the number of packets sent within a probe (see "services mpls-oam profile count") and the interval is the amount of time to wait between the packets within the probe ("services mpls-oam profile interval"). A probe is considered "lost" if all the LSP-ping packets within that probe have failed. You can configure the number of consecutive failed probes before generating a system event.

Only one system event is generated after the probe-loss threshold is crossed. The probe-loss counter is reset when you clear the event or a probe successfully reaches its destination.

To configure the number of consecutive failed probes for which system events will be generated:

**Command syntax: probe-loss consecutive-threshold [consecutive-threshold]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter             | Description                                                                      | Range | Default |
+=======================+==================================================================================+=======+=========+
| consecutive-threshold | threshold number of failed consecutive probes for which system events will be    | 0-64  | 2       |
|                       | generated                                                                        |       |         |
+-----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# probe-loss consecutive-threshold 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-mpls-oam-profile)# no probe-loss consecutive-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
