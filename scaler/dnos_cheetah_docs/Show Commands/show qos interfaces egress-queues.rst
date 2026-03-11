show qos interfaces egress-queues
---------------------------------

**Minimum user role:** viewer

You can view the state of the interface egress queues.



**Command syntax: show qos interfaces egress-queues [interface-name]**

**Command mode:** operational



**Note**

- The egress queues state is only available for the physical (and breakout) interfaces.
- egress-queues number is constant per interface, traffic class attachment per queue is not mandatory,
- packets which are not matched in any traffic class will go to the last egress-queue, any other queue which don't have traffic-class attached will not receive traffic

**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+
|    Parameter   |                                                                  Description                                                                  |                Range               |
+================+===============================================================================================================================================+====================================+
| interface-name | The name of the interface for which you want to display the QoS policy. If you do not specify an interface, all interfaces will be displayed. | ge<interface speed>-<A>/<B>/<C>    |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+


The following are the fields displayed for each interface:

+------------------------+-------------------------------------------------------------------------------------------+
| Field                  | Description                                                                               |
+========================+===========================================================================================+
| Interface              | The name of the interface                                                                 |
+------------------------+-------------------------------------------------------------------------------------------+
| queue type             | The egress queue forwarding class                                                         |
+------------------------+-------------------------------------------------------------------------------------------+
| Traffic class          | The Traffic class                                                                         |
+------------------------+-------------------------------------------------------------------------------------------+
| queue-size             | The egress queue total size in bytes                                                      |
+------------------------+-------------------------------------------------------------------------------------------+
| queue-current-usage    | The egress queue current usage in bytes                                                   |
+------------------------+-------------------------------------------------------------------------------------------+
| queue-usage-percentage | The egress queue current usage percentage                                                 |
+------------------------+-------------------------------------------------------------------------------------------+
| queue-max-usage        | The egress queue max usage since last reset in bytes                                      |
+------------------------+-------------------------------------------------------------------------------------------+
| queue-drops            | The egress queue total drops                                                              |
+------------------------+-------------------------------------------------------------------------------------------+


**Example**
::

    dnRouter# show qos interfaces egress-queues ge100-1/0/1

    Interface ge100-1/0/1:

      egress-queue-id 0:
        queue-type: sef
        Traffic-classes: Class-A
          Transmitted packets:                        295000
          Transmitted octets:                         6100000
          queue-size (bytes):                         1024000
          queue-current-usage (bytes):                102400
          queue-usage-percentage                      10%
          queue-max-usage (bytes)                     256000
          queue-max-usage-percentage                  25%
          queue-drops (packets)                       0
      
      egress-queue-id 1:
        queue-type: ef
        Traffic-classes: Class-B
          Transmitted packets:                        295000
          Transmitted octets:                         6100000
          queue-size (bytes):                         1024000
          queue-current-usage (bytes):                102400
          queue-usage-percentage                      10%
          queue-max-usage (bytes)                     128000
          queue-max-usage-percentage                  13%
          queue-drops (packets)                       0

      egress-queue-id 2:
        queue-type: hp
        Traffic-classes: Class-C
          Transmitted packets:                        295000
          Transmitted octets:                         6100000
          queue-size (bytes):                         1024000
          queue-current-usage (bytes):                1024
          queue-usage-percentage                      1%
          queue-max-usage (bytes)                     256000
          queue-max-usage-percentage                  25%
          queue-drops (packets)                       0

      egress-queue-id 3:
        queue-type: af/df
        Traffic-classes:
          Transmitted packets:                        295000
          Transmitted octets:                         6100000 
          queue-size (bytes):                         1024000
          queue-current-usage (bytes):                1024
          queue-usage-percentage                      1%
          queue-max-usage (bytes)                     256000
          queue-max-usage-percentage                  25%
          queue-drops (packets)                       0

    dnRouter# show qos interfaces egress-queues bundle-1

    ERROR: Unknown word: 'bundle-1'.


.. **Help line:** show QoS interfaces egress-queues


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
