show qos fabric-multicast counters
----------------------------------

**Minimum user role:** viewer

This command provides a view of the QoS policy counters on a fabric-multicast interface.

To display the QoS counters:

**Command syntax: show qos fabric-multicast counters** [interface-name]

**Command mode:** operational

**Parameter table**

+-------------------+-------------------------------------------------------------------+---------------------+
|                   |                                                                   |                     |
| Parameter         | Description                                                       | Range               |
+===================+===================================================================+=====================+
|                   |                                                                   |                     |
| interface-name    | Filter the displayed information to the specified interface.      | fabm-<A>/<B>/<C>    |
|                   |                                                                   |                     |
|                   |                                                                   | rcym-<A>/<B>/<C>    |
+-------------------+-------------------------------------------------------------------+---------------------+


**Example**
::

    dnRouter# show qos fabric-multicast counters fabm-5/0/0

    Interface fabm-5/0/0:
    Policy name: _ncp-to-fab   Direction: out

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

    dnRouter# show qos fabric-multicast counters rcym-5/0/0

    Interface rcym-5/0/0:
    Policy name: _fab-to-ncp   Direction: physical-out

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

.. **Help line:** show QoS counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+