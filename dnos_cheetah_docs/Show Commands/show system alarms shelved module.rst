show system alarms shelved module
---------------------------------

**Minimum user role:** viewer

To display the system alarms that are currently shelved in the system filtered by module name:



**Command syntax: show system alarms shelved module [module-name]** severity[severity-name] \| state[operator-state] \| shelve [shelve-name] \| severity[severity-name] state[operator-state] \| severity[severity-name] shelve [shelve-name] \| state[operator-state] shelve [shelve-name] \| severity[severity-name] state[operator-state] shelve [shelve-name]

**Command mode:** operational



**Parameter table**

The following information is displayed on each alarm:

+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Field             | Description                                                                                                                    | Range                    |
+===================+================================================================================================================================+==========================+
| details           | Displays detailed system alarms information, including operator state data.                                                    | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Name              | The alarm name                                                                                                                 | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Resource          | The resource the alarm is raised on                                                                                            | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Raise Time  | The time when the alarm was raised                                                                                             | yyyy-mm-ddThh:mm:ss      |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Message     | The alarm message                                                                                                              | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Severity          | The alarm severity                                                                                                             | warning, minor, major,   |
|                   |                                                                                                                                | critical                 |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Module Name       | The name of the alarm module                                                                                                   | dnos-alarms              |
|                   |                                                                                                                                | communications-alarm     |
|                   |                                                                                                                                | quality-of-service-alarm |
|                   |                                                                                                                                | processing-error-alarm   |
|                   |                                                                                                                                | equipment-alarm          |
|                   |                                                                                                                                | environmental-alarm      |
|                   |                                                                                                                                | bfd                      |
|                   |                                                                                                                                | bgp                      |
|                   |                                                                                                                                | efm-oam                  |
|                   |                                                                                                                                | management               |
|                   |                                                                                                                                | isis                     |
|                   |                                                                                                                                | pcep                     |
|                   |                                                                                                                                | ldp                      |
|                   |                                                                                                                                | l2vpn                    |
|                   |                                                                                                                                | aaa                      |
|                   |                                                                                                                                | rib                      |
|                   |                                                                                                                                | rsvp                     |
|                   |                                                                                                                                | segment-routing          |
|                   |                                                                                                                                | static-route             |
|                   |                                                                                                                                | fib-manager              |
|                   |                                                                                                                                | interfaces               |
|                   |                                                                                                                                | lacp                     |
|                   |                                                                                                                                | system                   |
|                   |                                                                                                                                | diagnostics              |
|                   |                                                                                                                                | platform                 |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Operator-state    | The state set by the operator                                                                                                  | ack, closed              |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

    dnRouter# show system alarms shelved module isis

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved
    
    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |          | ge100-0/0/4.200                      |                |
    

    dnRouter# show system alarms shelved module isis severity major

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |          | ge100-0/0/4.200                      |                |
    

    dnRouter# show system alarms shelved module isis state ack

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |


    dnRouter# show system alarms shelved module isis state closed

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |

   
    dnRouter# show system alarms shelved module isis shelve s1

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |          | ge100-0/0/4.200                      |                |
    

    dnRouter# show system alarms shelved  module isis state closed shelve s1

    System Totals Critical: 1  Major: 1  Minor: 0 Warning: 0
    2 alarms currently shelved

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |          | ge100-0/0/5.600                      | Closed         |


.. **Help line:** show active system alarms.

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 18.2    | Command introduced                               |
+---------+--------------------------------------------------+



