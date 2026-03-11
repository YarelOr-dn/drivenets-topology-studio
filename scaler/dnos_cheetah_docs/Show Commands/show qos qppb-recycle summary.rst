show qos qppb-recycle summary
-----------------------------

**Minimum user role:** viewer

This command provides a summary of qppb-recycle policy attached per interface, including counters.

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

**Command syntax: show qos qppb-recycle summary**

**Command mode:** operational

..
    **Internal note:**

    - Drop counters use the per-egress-queue drop counters

**Example**
::

    dnRouter# show qos qppb-recycle summary

    qppb-recycle
    Per NCP shaper rate:                 100000 Gbps
    Queue size:                          50000  kbytes

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | qppbr-0/0/0    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 0        | qppbr-0/0/1    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 0        | qppbr-0/0/2    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 0        | qppbr-0/0/3    |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | qppbr-1/0/0    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | 1        | qppbr-1/0/1    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | 1        | qppbr-1/0/2    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | 1        | qppbr-1/0/3    |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+


.. **Help line:** show summary of qppb-recycle policy including counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
