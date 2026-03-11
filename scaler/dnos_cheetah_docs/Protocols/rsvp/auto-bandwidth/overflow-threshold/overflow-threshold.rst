protocols rsvp auto-bandwidth overflow-threshold
------------------------------------------------

**Minimum user role:** operator

The overflow thresholds allows the tunnel to react quickly to significant changes in traffic volume. It uses the same mechanism as the adjust-threshold, except it operates at every sample-interval. The traffic rate is measured at every sampling-interval. If the traffic rate exceeds the configured threshold, a new LSP with updated bandwidth is signaled immediately. To configure the overflow threshold:

**Command syntax: overflow-threshold**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
- You can disable either thresholds (bandwidth or percent), but not both. When both thresholds are enabled, both thresholds must be crossed to adjust the bandwidth.

- A change to the overflow-threshold configuration will take effect on the next sampling.

- A change to the limit takes effect on the current sampling.

- If you do not specify a parameter, the default value is assumed.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# overflow-threshold bandwidth 100 percent 0
    dnRouter(cfg-protocols-rsvp-auto-bw)# overflow-threshold bandwidth 0 percent 10 limit 5
    dnRouter(cfg-protocols-rsvp-auto-bw)# overflow-threshold bandwidth 10 percent 5 limit 1
    dnRouter(cfg-protocols-rsvp-auto-bw)# overflow-threshold bandwidth 10 kbps percent 5 limit 1
    dnRouter(cfg-protocols-rsvp-auto-bw)# overflow-threshold bandwidth 10 kbps limit 2


**Removing Configuration**

To revert all overflow-threshold configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no overflow-threshold

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.0    | Command introduced     |
+---------+------------------------+
| 13.2    | Updated command syntax |
+---------+------------------------+
