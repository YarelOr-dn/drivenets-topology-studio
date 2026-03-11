protocols rsvp auto-bandwidth
-----------------------------

**Minimum user role:** operator

Tunnels reserve a fixed bandwidth based on the bandwidth setting, regardless of utilization. Auto-bandwidth allocation enables to dynamically adjust the bandwidth allocation based on the volume of traffic running through the tunnel. This allows the tunnel to reserve a minimum bandwidth and adjust the bandwidth as necessary, according to actual traffic patterns. The bandwidth adjustments do not interrupt traffic flow through the tunnel.
A tunnel with auto-bandwidth enabled is configured with a sampling interval. The traffic running through the tunnel is measured at each sampling interval and the average rate is calculated. At the end of the adjust-interval (AI) window, the highest average rate within the AI window (maxAvgRate) is compared against the configured adjust-threshold. The adjust-threshold sets the required difference before requesting a change in bandwidth. If maxAvgRate is below or above the threshold, the an attempt is made to signal a new path for the tunnel with the calculated maxAvg bandwidth.

The wider the AI window, the longer it takes to adjust to changes in traffic. Overflow and underflow thresholds allow the tunnel to react quickly to significant changes in traffic volume. These thresholds use the same mechanism as the adjust-threshold, except they operate at every sample-interval.
A new requested bandwidth reservation is always within the configured minimum and maximum limits. So if the sampled average rate is greater than the configured maximum, the requested bandwidth will be for the set maximum limit. Similarly, if the sampled average rate is lower than the configured minimum, the requested bandwidth will be for the configured minimum limit.

Once a new request for bandwidth is made, if the new path is successfully established, the old path is removed and the tunnel will switch over to the new path. Otherwise, the tunnel will continue using the existing path until the next sampling interval, when another attempt will be made to signal a new path.

The global configuration sets the default behavior for all tunnels. You can configure a specific behavior per tunnel using the rsvp tunnel auto-bandwidth hierarchy

To configure auto-bandwidth:

1.	Enable auto-bandwidth on tunnels.
2.	Configure the sampling interval (globally only).
3.	Configure adjust-interval and threshold.
4.	Configure overflow and underflow thresholds.
5.	Configure minimum and maximum bandwidth.
6.	Optional. Set the auto-bandwidth feature to monitor only.

To configure auto-bandwidth globally, enter auto-bandwidth configuration mode:

**Command syntax: auto-bandwidth**

**Command mode:** config

**Hierarchies**

- protocols rsvp
- protocols rsvp tunnel
- protocols rsvp auto-mesh tunnel-template

**Note**
.. -  rsvp auto-bandwidth global configuration set default behavior for all tunnel. when a tunnel is configured specific using "rsvp tunnel auto-bandwidth" the specific configuration takes precedence.

.. -  'no auto-bandwidth' restores all auto-bandwidth configuration to their default status and disables auto-bandwidth

- Auto-bandwidth parameters apply to primary headend tunnels (manual or auto-mesh) only. They do not apply to bypass tunnels (neither manual nor auto-bypass).

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)


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
