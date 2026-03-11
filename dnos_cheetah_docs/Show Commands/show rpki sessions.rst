show rpki sessions
------------------

**Minimum user role:** viewer

This command displays a detailed view of the configured BGP RPKI sessions with the local cache-servers in the system.

To display the rpki sessions:

**Command syntax: show rpki sessions** [server-address]

**Command mode:** operational


..
    **Internal Note**

    - support auto-complete for configured server-address

    - when 'server-address' is not specified, then detailed output per each configured server will be printed

    - filter by list key (server address)

**Parameter table**

+----------------+------------------------------------------+-------+---------+
| Parameter      | Description                              | Range | Default |
+================+==========================================+=======+=========+
| server-address | RPKI cache server IP address or hostname | \-    | \-      |
+----------------+------------------------------------------+-------+---------+

For each RPKI session, the following information is displayed:

+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Parameter           | Description                                                                                                    | Range              | Default   |
+=====================+================================================================================================================+====================+===========+
| Remote Address      | The configured remote address of the RPKI cache-server                                                         | IPv4/IPv6/Hostname | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Admin               | The administrative status, indicates whether the connection towards the RPKI cahce-server is currently enabled | Enabled            | Enabled   |
|                     |                                                                                                                | Disabled           |           |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Operational         | The RPKI session state, which is either Up or Down                                                             | Down               | \-        |
|                     |                                                                                                                | Up                 |           |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Uptime/Downtime     | The duration that the configured RPKI session is in its current state                                          | DD days, HH:MM:SS  | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Down reason         | The reason for the operational down state of the session                                                       | String             | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Transport protocol  | The transport protocol for the RPKI session                                                                    | SSH                | \-        |
|                     |                                                                                                                | TCP                |           |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Port                | The configured remote port of the RPKI cache-server                                                            | 1-65535            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Session-ID          | The uniquely generated ID that identifies the instance of the cache-server                                     | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Serial-ID           | The serial number is bound to the session ID and denotes the incremental logical version of the cache-server   | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Refresh interval    | The time BGP waits between periodic attempt to poll the cache-server and between subsequent attempts           | 1..86400           | 3600      |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Retry interval      | The time BGP waits for a response after sending a serial or reset query                                        | 1..7200            | 600       |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Expire interval     | The time BGP waits to keep records from a cache-server after the session drops                                 | 360..172800        | 7200      |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| IPv4/IPv6 Records   | The number of RPKI entries fetched from the RPKI cache-server and currently maintained in the local database   | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Connection attempts | The number of connection attempts                                                                              | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Connection failures | The number of failed connection attempts                                                                       | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Errors sent         | The number of errors sent to the RPKI cache-server                                                             | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Errors received     | The number of errors received from the RPKI cache-server                                                       | Integer            | \-        |
+---------------------+----------------------------------------------------------------------------------------------------------------+--------------------+-----------+

**Example**
::

    dnRouter# show rpki sessions 2.2.2.2

    BGP RPKI sessions:

    Remote Address: 2.2.2.2
        Admin state: disabled, Operational state: down, Uptime/Downtime: 2 days, 01:01:05
        Reason for down state: Connection was shut down by user
        Transport protocol: TCP, Port: 2211
        Session ID: 14720819, Serial ID: 3762
        Refresh interval: 3600 seconds
        Retry interval: 600 seconds
        Expire interval: 7200 seconds
        Active IPv4 records: 14513
        Active IPv6 records: 607
        Connection attempts: 1
        Connection failures: 0
        Errors sent: 0
        Errors received: 0


    dnRouter# show rpki sessions

    BGP RPKI sessions:

    Remote Address: 1.1.1.1
        Admin state: enabled, Operational state: up, Uptime/Downtime: 1 day, 01:01:05
        Transport protocol: SSH, Port: 323
        Session ID: 14720819, Serial ID: 3762
        Refresh interval: 3600 seconds
        Retry interval: 600 seconds
        Expire interval: 7200 seconds
        Active IPv4 records: 14513
        Active IPv6 records: 607
        Connection attempts: 1
        Connection failures: 0
        Errors sent: 0
        Errors received: 0

    Remote Address: 2.2.2.2
        Admin state: enabled, Operational state: up, Uptime/Downtime: 2 days, 01:01:05
        Transport protocol: TCP, Port: 2211
        Session ID: 14720819, Serial ID: 3762
        Refresh interval: 3600 seconds
        Retry interval: 600 seconds
        Expire interval: 7200 seconds
        Active IPv4 records: 14513
        Active IPv6 records: 607
        Connection attempts: 1
        Connection failures: 0
        Errors sent: 0
        Errors received: 0

    Remote Address: rpkiv.drivenets.com
        Admin state: enabled, Operational state: down, Uptime/Downtime: 0 days, 00:00:00
        Reason for down state: Pending connection
        Transport protocol: TCP, Port: 888
        Session ID: 14720820, Serial ID: 3762
        Refresh interval: 3600 seconds
        Retry interval: 600 seconds
        Expire interval: 7200 seconds
        Active IPv4 records: 14513
        Active IPv6 records: 607
        Connection attempts: 1
        Connection failures: 0
        Errors sent: 0
        Errors received: 0

.. **Help line:** show configured BGP RPKI sessions

**Command History**

+---------+------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                   |
+=========+================================================================================================+
| 15.1    | Command introduced                                                                             |
+---------+------------------------------------------------------------------------------------------------+
| 16.2    | Removed server-priority, added admin state information and replaced filter with server-address |
+---------+------------------------------------------------------------------------------------------------+
