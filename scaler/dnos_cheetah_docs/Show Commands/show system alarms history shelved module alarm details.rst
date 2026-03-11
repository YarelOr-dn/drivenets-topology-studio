show system alarms history shelved module alarm details
-------------------------------------------------------

**Minimum user role:** viewer

To display the system shelved alarms history with additional details on the recently cleared alarms in the system filtered by module name and alarm name:



**Command syntax: show system alarms history shelved module [module-name] alarm [alarm-name] details** severity[severity-name] \| state[operator-state] \| shelve [shelve-name] \| all-history-records \| severity[severity-name] state[operator-state] \| severity[severity-name] shelve [shelve-name] \| severity[severity-name] all-history-records \| state[operator-state] shelve [shelve-name] \| state[operator-state] all-history-records \| shelve [shelve-name] all-history-records \| severity[severity-name] state[operator-state] shelve [shelve-name] \| severity[severity-name] state[operator-state] all-history-records \| severity[severity-name] shelve [shelve-name] all-history-records \| state[operator-state] shelve [shelve-name] all-history-records \| severity[severity-name] state[operator-state] shelve [shelve-name] all-history-records

**Command mode:** operational



**Parameter table**

The following information is displayed on each alarm:

+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Field              | Description                                                                                                                    | Range                    |
+====================+================================================================================================================================+==========================+
| Name               | The alarm name                                                                                                                 | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Operator ID  | An operational alarm-id for updating the alarm state to acknowladged/closed, consumed by 'set alarm operator state' command    | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Resource           | The resource the alarm is raised on                                                                                            | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Raised Time  | The time when the alarm was raised                                                                                             | yyyy-mm-ddThh:mm:ss      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Cleared Time | The time when the alarm was cleared                                                                                            | yyyy-mm-ddThh:mm:ss      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Message      | The alarm message                                                                                                              | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Severity           | The alarm severity                                                                                                             | warning, minor, major,   |
|                    |                                                                                                                                | critical                 |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Module Name        | The name of the alarm module                                                                                                   | dnos-alarms              |
|                    |                                                                                                                                | communications-alarm     |
|                    |                                                                                                                                | quality-of-service-alarm |
|                    |                                                                                                                                | processing-error-alarm   |
|                    |                                                                                                                                | equipment-alarm          |
|                    |                                                                                                                                | environmental-alarm      |
|                    |                                                                                                                                | bfd                      |
|                    |                                                                                                                                | bgp                      |
|                    |                                                                                                                                | efm-oam                  |
|                    |                                                                                                                                | management               |
|                    |                                                                                                                                | isis                     |
|                    |                                                                                                                                | pcep                     |
|                    |                                                                                                                                | ldp                      |
|                    |                                                                                                                                | l2vpn                    |
|                    |                                                                                                                                | aaa                      |
|                    |                                                                                                                                | rib                      |
|                    |                                                                                                                                | rsvp                     |
|                    |                                                                                                                                | segment-routing          |
|                    |                                                                                                                                | static-route             |
|                    |                                                                                                                                | fib-manager              |
|                    |                                                                                                                                | interfaces               |
|                    |                                                                                                                                | lacp                     |
|                    |                                                                                                                                | system                   |
|                    |                                                                                                                                | diagnostics              |
|                    |                                                                                                                                | platform                 |
|                    |                                                                                                                                | transaction              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Operator State     | The state set by the operator                                                                                                  | ack, closed              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Operator Text      | The alarm resolution/actions as were described by the operator                                                                 | length 0..255 ascii char |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Operator Time      | The time when the operator acknowledged or closed the alarm                                                                    | yyyy-mm-ddThh:mm:ss      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-13T17:59:34 | 2022-10-14T17:59:54 | Major    | ISIS adjacency down on interface     |                |                                   |                     |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |                                   |                     |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details severity major

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-13T17:59:34 | 2022-10-14T17:59:54 | Major    | ISIS adjacency down on interface     |                |                                   |                     |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |                                   |                     |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details state ack

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Raised Time   | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details state closed

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details shelve s1

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-13T17:59:34 | 2022-10-14T17:59:54 | Major    | ISIS adjacency down on interface     |                |                                   |                     |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |                                   |                     |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details state closed shelve s1

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |


    dnRouter# show system alarms history shelved module isis alarm isis_neighbor_adjacency_down details all-history-records

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State | Operator Text                     | Operator Time       |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+-----------------------------------+---------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |                                   | 2022-10-13T18:59:44 |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         | handled the adjacency on the peer | 2022-10-12T19:15:40 |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-12T12:52:40 | 2022-10-13T12:52:40 | Major    | ISIS adjacency down on interface     |                |                                   |                     |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      |                |                                   |                     |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-13T17:59:34 | 2022-10-14T17:59:54 | Major    | ISIS adjacency down on interface     |                |                                   |                     |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |                                   |                     |


.. **Help line:** show system alarm history details.

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 18.0    | Command introduced                               |
+---------+--------------------------------------------------+
