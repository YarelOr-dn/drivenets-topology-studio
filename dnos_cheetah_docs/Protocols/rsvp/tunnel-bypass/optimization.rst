protocols rsvp tunnel bypass optimization
-----------------------------------------

**Minimum user role:** operator

LSPs may become suboptimal in time as topology changes occur or the availability of network resources changes. During this time, new paths that are less congested, with lower metrics, or with fewer hops may become available. An LSP with a fixed path cannot take advantage of new network resources. The LSP will remain fixed until a recalculation triggering change in the topology occurs. By enabling optimization, you can force the router to periodically recalculate paths for available tunnels and, if more optimal paths are found, make new decisions to reroute suboptimal LSPs through other paths. Optimization runs at fixed intervals or whenever an RSVP enabled interface becomes available.

To enable/disable optimization on the tunnel level:

**Command syntax: optimization [optimization]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass
- protocols rsvp tunnel
- protocols rsvp auto-mesh tunnel-template

**Note**
- Enabling optimization on a tunnel enables all types of optimization triggers, even if global optimization is disabled.

- Disabling the feature while optimization is running stops any current optimization attempts.

.. -  'no optimization [admin-state]' - return optimization admin-state to default value.

.. -  'no optimization' - return optimization admin-state to default value.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter    | Description                                                                      | Range        | Default |
+==============+==================================================================================+==============+=========+
| optimization | Run sequential path calculations for tunnels in UP state to find an optimized    | | enabled    | \-      |
|              | path                                                                             | | disabled   |         |
+--------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# optimization disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# optimization disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# tunnel
    dnRouter(cfg-rsvp-auto-bypass-tunnel)# optimization disabled


**Removing Configuration**

To revert all optimization configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no optimization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
