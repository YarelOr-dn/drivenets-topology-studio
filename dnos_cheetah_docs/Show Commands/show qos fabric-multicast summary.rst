show qos fabric-multicast summary
---------------------------------

**Minimum user role:** viewer

This command provides a summary of all fabric-multicast policies attached to interfaces, including counters.

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

**Command syntax: show qos fabric-multicast summary**

**Command mode:** operational

..
    **Internal note:**

    - Drop counters use the per-egress-queue drop counters

    - If NCP to fabric shaper is not configured by user, the shaper rate should be set to the default 1Tbs.

**Example**
::

    dnRouter# show qos fabric-multicast summary

    NCP to fabric
    Per NCP core shaper rate:             1200 Mpbs
    Queue size:                          50000 kbytes

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | fabm-0/0/0     |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | fabm-1/0/0     |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+


    Fabric to NCP
    Per NCP shaper rate:                 5000 Mpbs

    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | NCP      | Interface      |    Match[Mbps] |     Drop[Mbps] | Transmit[Mbps] |   Match[pkts] |     Drop[pkts] | Transmit[pkts] |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+
    | 0        | rcym-0/0/0     |        2842.99 |         264.75 |        2577.23 |     416683869 |       37710451 |      378973418 |
    | 1        | rcym-1/0/0     |          42.99 |              0 |          42.9  |        233869 |              0 |         233869 |
    | Total    |                |        2885.02 |         264.75 |        2577.23 |     416885532 |       37710451 |      378973418 |
    +----------+----------------+----------------+----------------+----------------+---------------+----------------+----------------+

.. **Help line:** show summary of all fabric-multicast policies attached to interfaces including counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+
