show qos srte-recycle summary
-----------------------------

**Minimum user role:** viewer

This command provides a summary of the SR-TE-recycle policy, attached per interface, including counters.

The following information is displayed per interface:

+-----------+-------------------------------------------------------------+
| Parameter | Description                                                 |
+===========+=============================================================+
| NCP       | The ID of the NCP                                           |
+-----------+-------------------------------------------------------------+
| Interface | The name of the interface to which a QoS policy is attached |
+-----------+-------------------------------------------------------------+
| Match     | The total number of matched packets/Mbps                    |
+-----------+-------------------------------------------------------------+
| Drop      | The total number of dropped packets/Mbps                    |
+-----------+-------------------------------------------------------------+
| Transmit  | The total transmit rate of packets/Mbps                     |
+-----------+-------------------------------------------------------------+

To display the QoS summary:

**Command syntax: show qos srte-recycle summary**

**Command mode:** operational

..
    **Internal note:**

    - Drop counters use the per-egress-queue drop counters

**Example**
::

    dnRouter# show qos srte-recycle  summary

    srte-recycle
    Per NCP shaper rate:                 100000 Gbps
    Queue size:                          50000  kbytes

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | srter-0/0/1    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | srter-1/0/1    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+


.. **Help line:** show summary of srte-recycle policy attached to interfaces including counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
