protocols rsvp auto-bandwidth underflow-threshold
-------------------------------------------------

**Minimum user role:** operator

The underflow thresholds allows the tunnel to react quickly to significant changes in traffic volume. It uses the same mechanism as the adjust-threshold, except it operates at every sample-interval. The traffic rate is measured at every sampling-interval. If the traffic rate drops below the configured threshold, a new LSP with updated bandwidth is signaled immediately. To configure the overflow threshold:

**Command syntax: underflow-threshold**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
- You can disable either thresholds (bandwidth or percent), but not both. When both thresholds are enabled, both thresholds must be crossed to adjust the bandwidth.

- A change to the underflow-threshold configuration will take effect on the next sampling.

- A change to the limit takes effect on the current sampling.

- If you do not specify a parameter, the default value is assumed.

..-  must set either bandwidth or percent to enable threshold feature.
..
..-  when both bandwidth and percent are configured with a non-zero value, perform bandwidth adjustments when **both** terms are met.
..
..-  Units can only be set with bandwidth
..
..-  'underflow-threshold' , 'no underflow-threshold', 'no underflow-threshold bandwidth percent limit' - return bandwidth and percent to their default values
..
..-  'no underflow-threshold bandwidth' - return bandwidth to its default value
..
..-  'no underflow-threshold percent - return percent to its default value
..
..-  'no underflow-threshold limit - return limit to its default value

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# underflow-threshold bandwidth 100 percent 0
    dnRouter(cfg-protocols-rsvp-auto-bw)# underflow-threshold bandwidth 0 percent 10 limit 5
    dnRouter(cfg-protocols-rsvp-auto-bw)# underflow-threshold bandwidth 10 percent 5 limit 1
    dnRouter(cfg-protocols-rsvp-auto-bw)# underflow-threshold bandwidth 10 kbps percent 5 limit 1


**Removing Configuration**

To revert all underflow-threshold configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no underflow-threshold

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.0    | Command introduced     |
+---------+------------------------+
| 13.2    | Updated command syntax |
+---------+------------------------+
