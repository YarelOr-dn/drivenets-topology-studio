show qos vrf-redirect summary
---------------------------------

**Minimum user role:** viewer

This command provides a summary of all vrf-redirect policies attached per interface, including counters.

The following information is displayed per interface:
+-----------+-------------------------------------------------------------+---------------+-----------------+
| Parameter | Description                                                 | Range         | Default         |
+===========+=============================================================+===============+=================+
| NCP       | The ID of the NCP                                           |               | /-              |
+-----------+-------------------------------------------------------------+---------------+-----------------+
| Interface | The name of the interface to which a QoS policy is attached |               | /-              |
+-----------+-------------------------------------------------------------+---------------+-----------------+
| Match     | The total number of matched packets/Mbps                    |               | /-              |
+-----------+-------------------------------------------------------------+---------------+-----------------+
| Drop      | The total number of dropped packets/Mbps                    |               | /-              |
+-----------+-------------------------------------------------------------+---------------+-----------------+
| Transmit  | The total transmit rate of packets/Mbps                     |               | /-              |
+-----------+-------------------------------------------------------------+---------------+-----------------+

To display the QoS summary:

**Command syntax: show qos vrf-redirect summary**

**Command mode:** operational

..
    **Internal note:**

    - Drop counters use the per-egress-queue drop counters

    - If vrf-redirect shapers are not configured by user, the shaper rate should be set to the default 100Gbps.

**Example**
::

    dnRouter# show qos vrf-redirect summary

    vrf-redirect-0
    Per NCP shaper rate:                 100000 Gbps
    Queue size:                          50000  kbytes

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | vrfr0-0/0/0    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | vrfr0-1/0/0    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+


    vrf-redirect-1
    Per NCP shaper rate:                 200000 Gbps
    Queue size:                          50000  kbytes

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | vrfr1-0/0/0    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | vrfr1-1/0/0    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+

.. **Help line:** show summary of all vrf-redirect policies attached to interfaces including counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
