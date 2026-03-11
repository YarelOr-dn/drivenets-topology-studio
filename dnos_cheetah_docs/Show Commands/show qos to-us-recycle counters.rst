show qos to-us-recycle counters
-------------------------------

**Minimum user role:** viewer

This command provides a view of the QoS policy counters for packets that are recycled as part of traffic forwarding over the SR-TE policy.

To display the QoS counters:

**Command syntax: show qos to-us-recycle counters** [ncp-id]

**Command mode:** operational

**Parameter table**

+--------------------------+-------------------------------------------------------------------+---------------------+
|                          |                                                                   |                     |
| Parameter                | Description                                                       | Range               |
+==========================+===================================================================+=====================+
|                          |                                                                   |                     |
| ncp-id                   | Filter the displayed information to the specified ncp.            | range of ncp-ids    |
|                          |                                                                   | 0..48               |
|                          |                                                                   |                     |
+--------------------------+-------------------------------------------------------------------+---------------------+

**Example**
::

    dnRouter# show qos to-us-recycle counters 5


    Interface to-usr-5/0/1:
     Rule default
       Matched packets:                                  300000 (        4233 pps /       0 Mpps )
       Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
       Transmitted packets:                              295000 (          13 pps /       0 Mpps )
       Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
       Dropped packets:                                    5000 (          13 pps /       0 Mpps )
       Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

       Queue statistics:
        Current queue size (kbytes):                        800
        Average queue size (kbytes):                        800

.. **Help line:** show QoS counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
