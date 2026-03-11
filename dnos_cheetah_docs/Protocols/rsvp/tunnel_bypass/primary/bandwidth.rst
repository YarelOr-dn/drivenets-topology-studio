protocols rsvp tunnel bypass primary bandwidth
----------------------------------------------

**Minimum user role:** operator

This command reserves the bandwidth on the tunnel. When a bandwidth reservation is configured, reservation messages propagate the bandwidth value throughout the tunnel. Routers must reserve the bandwidth specified across the link for the particular LSP. The reservation is done independently of the traffic that runs through the tunnel.

To configure the bandwidth requirements for the tunnel, manual bypass tunnel, or auto-bypass tunnel:

**Command syntax: bandwidth [bandwidth-value]** [bandwidth-units]

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary

**Note**
- The total bandwidth cannot exceed the bandwidth ranges.

- Reconfiguring the tunnel's bandwidth will reset the tunnel, unless "soft preemption" is configured.

.. -  tunnel bandwidth 0 mbps will result in 0 BW reservation for a tunnel (best-effort traffic). Tunnels with 0 bandwidth setting can be allocated on every bandwidth pool (matching .. their class) even if the pool is with 0 bandwidth. This applies toalltunnel types
..
.. -  considering **bandwidth units,** total bandwidth amount cannot exceed 4294967295 kbps. i.e for mbps max range is 4194303, for gbps 4096
..
.. -  reconfiguring tunnel bandwidth will reset the tunnel, unless "soft preemption" is configured
..
.. -  'no bandwidth [bandwidth] kbps' - return to default units
..
.. -  'no bandwidth' - set tunnel to default 0 mbps bandwidth

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter       | Description                                                                      | Range        | Default |
+=================+==================================================================================+==============+=========+
| bandwidth-value | Tunnel bandwidth value                                                           | 0..4294967295| 0       |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| bandwidth-units | The units used for bandwidth. If you do not specify the unit, mpbs will be used. | kbps         | mbps    |
|                 |                                                                                  | mbps         |         |
|                 |                                                                                  | gbps         |         |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# bandwidth 10000 kbps

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# bandwidth 20000


**Removing Configuration**

To revert to the default tunnel bandwidth reservation (i.e. 0 mbps):
::

    dnRouter(cfg-rsvp-tunnel-primary)# no bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
