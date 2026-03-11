show qppb policy summary
------------------------------

**Minimum user role:** viewer

The per rule counters view for the installed QPPB policy.

To display the QPPB rules counters:



**Command syntax: show qppb policy summary**

**Command mode:** operational



**Note**

- The counters are the total for each rule of the per interface per rule counters displayed with the show qppb interfaces counters.


The following are the fields displayed for each rule:

+------------------------+-------------------------------------------------------------------------------------------+
| Field                  | Description                                                                               |
+========================+===========================================================================================+
| Policy name            | The name of the policy                                                                    |
+------------------------+-------------------------------------------------------------------------------------------+
| Rule                   | The rule ID                                                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| Match                  | The number of packets that matched the rule                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| Drop                   | The number of packets that were dropped                                                   |
+------------------------+-------------------------------------------------------------------------------------------+
| Tx                     | The number of packets that were transmitted                                               |
+------------------------+-------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show qppb rules counters

    QPPB Interface and Rule counters:
    Policy Name: Policy-1


    | Rule Id  | Match [Mbps] | Drop [Mbps] | TX[Mbps]  | Match [pkts] | Drop [pkts] | TX[pkts]
    +----------+--------------+-------------+-----------+--------------+-------------+----------+
    | 10       | 20           | 0           | 20        | 500          | 0           | 500      |
    | 20       | 30           | 0           | 30        | 57680        | 0           | 57680    |
    | 105      | 100          | 24          | 76        | 7801         | 11          | 7790     |



.. **Help line:** show QPPB rules counters


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
