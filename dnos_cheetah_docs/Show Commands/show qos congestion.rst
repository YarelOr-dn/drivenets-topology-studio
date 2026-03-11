show qos congestion
-------------------

**Minimum user role:** viewer

The command is optimized to run together with the **monitor** command to provide a unix top-like behavior, to observe the congestion condition as it develops. **include** or **exclude** pipe commands can be used to monitor a specific traffic class or specific egress interface. Similar to top, both primary sort and secondary sort options are available. The maximal number of lines can be set to fit the screen size for a stable output when used in combination with monitor pipe command.

The Top 3 information provides summary statistics of the congestion table. The sum of all congested voq of the same traffic class is summarized, and the first 3 most congested traffic classes are displayed. Similarly the first 3 egress interfaces, the first 3 queues, the first 3 NCPs and the first 3 cores are displayed as well.

To display a list of most congested voqs.


**Command syntax: show qos congestion** ncp [ncp-id] sort [sort-by] ssort [ssort-by] lines [line-num] top-3 [top-3]

**Command mode:** operational

**Note**


**Parameter table**

+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+
|              |                                                                                                                                          |                                                    |            |
| Parameter    | Description                                                                                                                              | Range                                              | Default    |
+==============+==========================================================================================================================================+====================================================+============+
|              |                                                                                                                                          |                                                    |            |
| Ncp-id       | Filter the displayed information   to the specified NCP.                                                                                 | 0..191                                             | \-         |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+
|              |                                                                                                                                          |                                                    |            |
| Sort-by      | Select a primary sorting criterion.                                                                                                      | ncp: increasing ncp-ids and   core-ids             | ncp        |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-id: increasing voq id                          |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | if-name: increasing interface   names              |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | que-id: increasing Q number                        |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-b: decreasing voq occupancy in   bytes         |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-p: decreasing voq occupancy in   %             |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | que-b: decreasing if queue   occupancy in bytes    |            |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+
|              |                                                                                                                                          |                                                    |            |
| Ssort-by     | Select a secondary sorting   criterion                                                                                                   | ncp: increasing ncp-ids and   core-ids             | Voq-b      |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-id: increasing voq id                          |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | if-name: increasing interface   names              |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | que-id: increasing Q number                        |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-b: decreasing voq occupancy in   bytes         |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | voq-p: decreasing voq occupancy in   %             |            |
|              |                                                                                                                                          |                                                    |            |
|              |                                                                                                                                          | que-b: decreasing if queue   occupancy in bytes    |            |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+
|              |                                                                                                                                          |                                                    |            |
| line-num     | The maximumum number of lines to   display in the congestion table.                                                                      | 1..3072                                            | 16         |
|              |                                                                                                                                          |                                                    |            |
|              | Set the maximum to match the   number of lines in the terminal when using the command in combination with the   monitor pipe command.    |                                                    |            |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+
|              |                                                                                                                                          |                                                    |            |
| Top-3        | Include or exclude top-3 information                                                                                                     | enable | disable | only                            | enable     |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+------------+

The following information is displayed:

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Field            | Description                                                                                                                                                                         |
+==================+=====================================================================================================================================================================================+
|                  |                                                                                                                                                                                     |
| NCP              | The NCP ID                                                                                                                                                                          |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Core             | The core ID                                                                                                                                                                         |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| VOQ              | The VOQ ID                                                                                                                                                                          |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Interface        | The egress interface name                                                                                                                                                           |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Q                | The internal queue number on the   egress interface                                                                                                                                 |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Traffic Class    | The traffic class name of the rule   controlling the queue, if a policy rule is attached to the interface                                                                           |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| VOQ[Bytes]       | The size of the current VOQ size   in bytes                                                                                                                                         |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| VOQ[%]           | The VOQ current occupancy in   percentage relative to the maximal set queue size                                                                                                    |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                  |                                                                                                                                                                                     |
| Queue[Bytes]     | An approximation of the total   virtual queue size. I.e., the sum of all congested VOQs with the same VOQ-IDs   from all NCPs and cores that feed the same egress virtual queue.    |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show qos congestion sort voq-b

    Top 3:
    Traffic Class: RealTime 38000000, BestEffort 140000000, VPNservice 1900
    Interface: ge100-1/0/1 52000000, ge10-3/0/2/1 1900
    Queue: ge100-1/0/1-3 38000000, ge100-1/0/1-4 140000000
    NCP: NCP-1 380000000, NCP-2 9000000, NCP-4 600000
    Core: NCP-1-0 270001900, NCP-1-1 240000000, NCP-2-0 9000000


    | NCP | Core | VOQ   | Interface     | Q | Traffic Class | VOQ[Bytes]   | VOQ[%] | Queue[Bytes] |
    +-----+------+-------+---------------+---+---------------+--------------+--------+--------------+
    | 1   | 0    |  1672 | ge100-1/0/1   | 3 | RealTime      |    270000000 | 97.2%  |    380000000 |
    | 1   | 1    |  1673 | ge100-1/0/1   | 4 | BestEffort    |    140000000 | 40.2%  |    140000000 |
    | 1   | 1    |  1672 | ge100-1/0/1   | 3 | RealTime      |    100000000 | 47.3%  |    380000000 |
    | 2   | 0    |  1672 | ge100-1/0/1   | 3 | RealTime      |      9000000 | 97.2%  |    380000000 |
    | 4   | 1    |  1672 | ge100-1/0/1   | 3 | RealTime      |       600000 | 97.2%  |    380000000 |
    | 3   | 0    |  1672 | ge100-1/0/1   | 3 | RealTime      |       400000 | 97.2%  |    380000000 |
    | 1   | 0    | 11302 | ge10-3/0/2/1  | 2 | VPNservice    |         1900 |  2.2%  |         1900 |

.. **Help line:** show a list of most congested voqs

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+