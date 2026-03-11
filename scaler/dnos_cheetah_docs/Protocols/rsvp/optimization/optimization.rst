protocols rsvp optimization
---------------------------

**Minimum user role:** operator

LSPs may become suboptimal in time as topology changes occur or the availability of network resources changes. During this time, new paths that are less congested, with lower metrics, or with fewer hops may become available. An LSP with a fixed path cannot take advantage of new network resources. The LSP will remain fixed until a recalculation triggering change in the topology occurs. By enabling optimization, you can force the router to periodically recalculate paths for available tunnels and, if more optimal paths are found, make new decisions to reroute suboptimal LSPs through other paths. Optimization runs at fixed intervals or whenever an RSVP enabled interface becomes available.
Optimization is applicable to all tunnel types. Tunnels are optimized sequentially, from the lowest priority and highest bandwidth to highest priority and lowest bandwidth. The optimization is aggressive: the tunnel will be optimized only if a new path has a better metric to the destination.
If optimization fails, no additional optimization is attempted until the next scheduled optimization cycle or until a manual clear rsvp tunnels optimize is performed (see "clear rsvp tunnels").

To configure the optimization options, enter the global RSVP optimization configuration mode:

**Command syntax: optimization**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  disabling optimization while optimization is in process will stop current optimization attempts

.. -  reconfiguring optimize-timer while timer is running, will reset optimize-timer to new interval value. if optimization was underway, stop current optimization process (even if optimization is due to interface up or user clear triggers).

.. -  'no optimization'- returns all optimization configuration to their default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)


**Removing Configuration**

To revert all optimization configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no optimization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
