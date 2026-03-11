show system telemetry
---------------------

**Minimum user role:** viewer

To display summary of dial-out telemetry:


**Command syntax: show system telemetry**

**Command mode:** operational

**Parameter table**

The following parameters are displayed as the summary of dial-out telemetry:

Subscriptions Overview

+-----------------------+-----------------------------------------------------------------------------+
| Parameter             | Description                                                                 |
+=======================+=============================================================================+
| Subscription Total    | The total count of all subscriptions that have been                         |
|                       | configured in the system                                                    |
+-----------------------+-----------------------------------------------------------------------------+
| Subscription Active   | The number of subscriptions that are currently active, each having at least |
|                       | one active destination associated with it and one resolved yang-path        |
+-----------------------+-----------------------------------------------------------------------------+
| Subscription Disabled | The count of subscriptions that are administratively disabled,              |
|                       | including those affected by a global admin state disabled action            |
+-----------------------+-----------------------------------------------------------------------------+

Destinations Overview

+--------------------------+----------------------------------------------------------------------------------+
| Parameter                | Description                                                                      |
+==========================+==================================================================================+
| Destination Groups       | The total number of destinations groups                                          |
+--------------------------+----------------------------------------------------------------------------------+
| Destinations Total       | The aggregate count of all defined destinations within the system, including any |
|                          | repetitions of the same destination in different groups                          |
+--------------------------+----------------------------------------------------------------------------------+
| Destinations Active      | The count of distinct destinations currently receiving telemetry data from       |
|                          | at least one subscription.                                                       |
|                          | Multiple subscriptions to the same destination are counted once                  |
+--------------------------+----------------------------------------------------------------------------------+
| Destinations Sessions    | The total number of active telemetry sessions established for data transmission, |
|                          | with a single destination potentially having multiple sessions                   |
+--------------------------+----------------------------------------------------------------------------------+

Sensor Paths Overview

+-----------------------------+-------------------------------------------------------------------------+
| Parameter                   | Description                                                             |
+=============================+=========================================================================+
| Sensor Groups Total         | The total number of configured sensor groups within the system          |
+-----------------------------+-------------------------------------------------------------------------+
| Sensor Paths Total          | The complete count of sensor paths defined across all sensor groups,    |
|                             | considering duplicate entries                                           |
+-----------------------------+-------------------------------------------------------------------------+
| Sensor Paths Unique         | The total number of unique sensor paths within the system               |
|                             | after removing any duplicates from the count                            |
+-----------------------------+-------------------------------------------------------------------------+
| Sensor Paths Active         | The quantity of sensor paths that are currently being collected,        |
|                             | including any paths that are duplicated across different sensor groups  |
+-----------------------------+-------------------------------------------------------------------------+
| Sensor Paths Not Resolved   | The number of sensor paths that the system has been unable to resolve,  |
|                             | including duplicate unresolved paths                                    |
+-----------------------------+-------------------------------------------------------------------------+

Exported Telemetry Statistics

+---------------------+-----------------------------------------------------------------------------------+
| Parameter           | Description                                                                       |
+=====================+===================================================================================+
| Exported bit rate   | The rate at which telemetry data is being exported from the system,               |
|                     | measured in Mbps (megabits per second)                                            |
+---------------------+-----------------------------------------------------------------------------------+
| Exported leaves     | The total number of telemetry leaves that have been successfully                  |
|                     | exported from the system                                                          |
+---------------------+-----------------------------------------------------------------------------------+
| Exported leaf rate  | The rate at which telemetry leaves are being exported,                            |
|                     | measured in leaves per second                                                     |
+---------------------+-----------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show system telemetry

    Subscriptions         Total:    1      Active:    1     Disabled:    0
    Destination Groups    Total:    2
    Destinations          Total:    4      Active:    2     Sessions:    2
    Sensor Groups         Total:    2
    Sensor Paths          Total:    3      Active:    1     Not Resolved:    1     Unique:    2

    Dial-Out Telemetry Statistics:
      Exported bit rate: 1.2 Mbps
      Exported leaves: 25,000
      Exported leaf rate: 32 leaves per second

.. **Help line:** show system telemetry

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.10   | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
