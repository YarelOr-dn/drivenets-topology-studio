show system ftp sessions
-------------------------

**Minimum user role:** viewer

To display all active FTP sessions in the system:



**Command syntax: show system ftp sessions**

**Command mode:** operational



**Parameter table**

For each active session, the following information is displayed:

+----------------+-------------------------------------------------------+-----------------------------+
| Parameter      | Description                                           | Range                       |
+================+=======================================================+=============================+
| Session-ID     | The socket ID                                         | 1..65535                    |
+----------------+-------------------------------------------------------+-----------------------------+
| User           | The FTP user name                                     | String                      |
+----------------+-------------------------------------------------------+-----------------------------+
| VRF            | The FTP session management type (in-band/out-of-band) | default (in-band)           |
|                |                                                       | mgmt0 (out-of-band)         |
+----------------+-------------------------------------------------------+-----------------------------+
| Role           | The type of role                                      | Admin                       |
|                |                                                       | Operator                    |
|                |                                                       | Viewer                      |
|                |                                                       | Techsupport                 |
+----------------+-------------------------------------------------------+-----------------------------+
| Remote Address | The address of the client that opened the FTP session | X.X.X.X:Y                   |
|                |                                                       | X.X.X.X - IPv4/IPv6 address |
|                |                                                       | Y - TCP port number         |
+----------------+-------------------------------------------------------+-----------------------------+
| Session Uptime | The timestamp of the session                          | DD days, HH:MM:SS           |
+----------------+-------------------------------------------------------+-----------------------------+
| Idle time      | The amount of time the session is idle                | HH:MM:SS                    |
+----------------+-------------------------------------------------------+-----------------------------+

**Example**
::

    dnRouter# show system ftp sessions

    FTP Server Sessions:

    |   Session-ID | User   | Role      |Vrf         | Remote Address   | Session Uptime   | Idle time  |
    |--------------+--------+-----------+------------+------------------+------------------+------------|
    |          714 | dnroot | Admin     | default    | 2.2.2.2:56356    | 1 day, 01:01:05  | 01:02:05   |
    |          748 | dnroot | Admin     | default    | 2.2.2.3:56364    | 2 days, 01:01:05 | 00:02:05   |
    |          777 | user1  | Operator  | mgmt0      | 3.4.2.3:43564    | 0 days, 05:21:20 | 00:00:10   |

.. **Help line:** show active ftp sessions in system.

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 11.6    | Command introduced                                            |
+---------+---------------------------------------------------------------+
| 13.1    | Added OOB support: VRF type (in-band/out-of-band) per session |
+---------+---------------------------------------------------------------+


