protocols rsvp auto-mesh tunnel-template auto-bandwidth adjust-threshold
------------------------------------------------------------------------

**Minimum user role:** operator

At the end of the adjust-interval (AI) window, the highest average rate within the AI window (maxAvgRate) is compared against the configured adjust-threshold. The adjust-threshold sets the required difference before requesting a change in bandwidth. If maxAvgRate is below or above the threshold, then an attempt is made to signal a new path for the tunnel with the calculated maxAvg bandwidth.
To configure the threshold:

**Command syntax: adjust-threshold**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template auto-bandwidth
- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth

**Note**
- You can disable either thresholds (bandwidth or percent), but not both. When both thresholds are enabled, both thresholds must be crossed to adjust the bandwidth.

- A change to the adjust-threshold configuration will take effect on the next sampling.

.. -  set bandwidth=0 or percent=0 to ignore one of the terms.

.. -  cannot set both bandwidth and percent to 0

.. -  when both bandwidth and percent are configured with a non-zero value, perform bandwidth adjustments when **both** terms are met.

.. -  Units can only be set with bandwidth

.. -  'adjust-threshold' , 'no adjust-threshold', 'no adjust-threshold bandwidth percent' - return bandwidth and percent to their default values

.. -  'no adjust-threshold bandwidth' - return bandwidth to its default value

.. -  'no adjust-threshold percent - return percent to its default value

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# adjust-threshold bandwidth 100 mbps percent 0
    dnRouter(cfg-protocols-rsvp-auto-bw)# adjust-threshold bandwidth 0 percent 10
    dnRouter(cfg-protocols-rsvp-auto-bw)# adjust-threshold bandwidth 10 kbps percent 5
    dnRouter(cfg-protocols-rsvp-auto-bw)# adjust-threshold bandwidth 20 percent 0


**Removing Configuration**

dnRouter(cfg-protocols-rsvp-auto-bw)# no adjust-threshold bandwidth
::

    dnRouter(cfg-protocols-rsvp)# no adjust-threshold

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.0    | Command introduced     |
+---------+------------------------+
| 13.2    | Updated command syntax |
+---------+------------------------+
