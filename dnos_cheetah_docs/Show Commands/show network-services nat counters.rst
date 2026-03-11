show network-services nat counters
----------------------------------

**Minimum user role:** operator

**Description:** To display the NAT instance counters:


**Command syntax: show network-services nat counters [instance-name]**

**Command mode:** operational

**Parameter table**

+----------------+-------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                             | Range  | Default |
+================+=========================================================================+========+=========+
| instance-name  | NAT instance name                                                       | String | \-      |
+----------------+-------------------------------------------------------------------------+--------+---------+

**Note**

The following counters presented by “show network-services nat counters” refer to the interface counters and not to NAT instance counters:
Outbound statistics
- Total frames RX (rate)
- Total L3 dropped packets
- Total frames TX (rate)
Inbound statistics
- Total frames RX (rate)
- Total L3 dropped packets
- Total frames TX (rate)

The above counters are presented as part of the “show network-services nat counters” output for operational simplicity sake. The above counters are not cleared by triggering “clear nat counters” command. To clear the above counters, the user must use the “clear interface counters” command.

**Example**
::

        dnRouter# show network-services nat counters nat-att-pepsi

        Outbound Statistics (nat-0):
         Total frames RX (rate):                       123145    (1230000 fps / 1200 Mfps)
         Total L3 dropped packets:                     123123123
         Total NAT dropped packets:                    123123
         NAPT exhausted range drop:                    12312
         NAT exhausted range drop:                     12312
         Fragmented session mismatch drop:             123123
         Fragment exhausted range drop:                122312
         NAT session table full drop:                  1212234
         Total frames TX (rate):                       123145    (1230000 fps / 1200 Mfps)

        Inbound Statistics (nat-1):
         Total frames RX (rate):                       123145    (1230000 fps / 1200 Mfps)
         Total L3 dropped packets:                     12123
         Total NAT dropped packets:                    123123123
         Fragmented session mismatch drop:             123123
         NAT session mismatch drop:                    123123
         NAPT session mismatch drop:                   123123
         ICMP session mismatch drop:                   123123
         Fragment exhausted range drop:                123123
         Total frames TX (rate):                       123145    (1230000 fps / 1200 Mfps)

        Instance Statistics:
         Total forwarded w/o translation:              123123
         Total number of translation rules:            500
         Number of static SNAT44 rules:                 10
         Number of static SNAPT44 rules:                10
         Number of static DNAT44 rules:                 10
         Number of static DNAPT44 rules:                10
         Number of dynamic SNAT44 rules:                100
         Number of dynamic SNAPT44 rules:               390
         Total number of active sessions:              50000
         Number of active NAT44 sessions:              40000
         Number of active TCP NAPT44 sessions:         996
         Number of active UDP NAPT44 sessions:         2
         Number of active ICMP NAPT44 sessions:        2
         Number of active Fragment sessions:           2
         Total rate of new NAT44/NAPT44 sessions:      1000 per second
         Total rate of expired NAT44/NAPT44 sessions:  950 per second

.. **Help line:** show network-services nat counters [nat-instance]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
