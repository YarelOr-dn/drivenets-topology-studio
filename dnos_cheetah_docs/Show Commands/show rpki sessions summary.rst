show rpki sessions summary
--------------------------

**Minimum user role:** viewer

To display a summary of all BGP RPKI sessions:

**Command syntax: show rpki sessions summary**

**Command mode:** operational



For each RPKI session, the following information is displayed:

+-------------------+----------------------------------------------------------------------------------------------------------------+
| Parameter         | Description                                                                                                    |
+===================+================================================================================================================+
| Remote Address    | The configured RPKI session remote address and port                                                            |
+-------------------+----------------------------------------------------------------------------------------------------------------+
| Admin             | The administrative status, indicates whether the connection towards the RPKI cahce-server is currently enabled |
+-------------------+----------------------------------------------------------------------------------------------------------------+
| Operational       | The RPKI session state, which is either Up or Down                                                             |
+-------------------+----------------------------------------------------------------------------------------------------------------+
| Uptime/Downtime   | The duration that the configured RPKI session is in its current state                                          |
+-------------------+----------------------------------------------------------------------------------------------------------------+
| IPv4/IPv6 Records | The number of RPKI entries fetched from the RPKI cache-server and currently maintained in the local database   |
+-------------------+----------------------------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show rpki sessions summary

    BGP RPKI sessions:

    | Remote Address          | Admin    | Operational | Uptime/Downtime   | IPv4 Records | IPv6 Records |
    +-------------------------+----------+-------------+-------------------+--------------+--------------+
    | 1.1.1.1:323             | enabled  | up          | 1 day, 01:01:05   | 14513        | 607          |
    | 2.2.2.2:2211            | disabled | down        | 2 days, 01:01:05  | 0            | 0            |
    | rpkiv.drivenets.com:888 | enabled  | down        | 0 days, 01:01:05  | 0            | 200          |

    Number of BGP RPKI sessions: 3
    Total number of IPv4 records: 14513
    Total number of IPv6 records: 807

.. **Help line:** show BGP RPKI sessions summary

**Command History**

+---------+-------------------------------------------------------------------+
| Release | Modification                                                      |
+=========+===================================================================+
| 15.1    | Command introduced                                                |
+---------+-------------------------------------------------------------------+
| 16.2    | Removed server priority and added admin state column to the table |
+---------+-------------------------------------------------------------------+
