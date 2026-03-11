protocols rsvp auto-mesh tunnel-template auto-bandwidth
-------------------------------------------------------

**Minimum user role:** operator

LSPs may become suboptimal in time as topology changes occur or the availability of network resources changes. During this time, new paths that are less congested, with lower metrics, or with fewer hops may become available. An LSP with a fixed path cannot take advantage of new network resources. The LSP will remain fixed until a recalculation triggering change in the topology occurs. By enabling auto-bandwidth, you can force the router to periodically recalculate paths for available tunnels and, if more optimal paths are found, make new decisions to reroute suboptimal LSPs through other paths. Optimization runs at fixed intervals or whenever an RSVP enabled interface becomes available.
Optimization is applicable to all tunnel types. Tunnels are optimized sequentially, from the lowest priority and highest bandwidth to highest priority and lowest bandwidth. The auto-bandwidth is aggressive: the tunnel will be optimized only if a new path has a better metric to the destination.
If auto-bandwidth fails, no additional auto-bandwidth is attempted until the next scheduled auto-bandwidth cycle or until a manual clear rsvp tunnels optimize is performed (see "clear rsvp tunnels").

To configure the auto-bandwidth options, enter the global RSVP auto-bandwidth configuration mode:

**Command syntax: auto-bandwidth**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp
- protocols rsvp tunnel

**Note**
.. -  disabling auto-bandwidth while auto-bandwidth is in process will stop current auto-bandwidth attempts

.. -  reconfiguring optimize-timer while timer is running, will reset optimize-timer to new interval value. if auto-bandwidth was underway, stop current auto-bandwidth process (even if auto-bandwidth is due to interface up or user clear triggers).

.. -  'no auto-bandwidth'- returns all auto-bandwidth configuration to their default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bandwidth)


**Removing Configuration**

To revert all auto-bandwidth configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no auto-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
