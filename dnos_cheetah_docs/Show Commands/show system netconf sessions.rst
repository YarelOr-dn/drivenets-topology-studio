show system netconf sessions
-----------------------------

**Minimum user role:** viewer

To display all active NETCONF sessions in the system:



**Command syntax: show system netconf sessions**

**Command mode:** operational



.. **Internal Note**

    Counters:

    - In rpcs - Number of correct <rpc> messages received.

    - In bad rpcs - Number of messages received when an <rpc> message was expected, that were not correct <rpc> messages. This includes XML parse errors and errors on the rpc layer.

    - Out rpc errors - Number of <rpc-reply> messages sent that contained an <rpc-error> element.

    - no vrf and remote address info for internal connections.


**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Parameter      | Description                                                                                                                    | Range               |
+================+================================================================================================================================+=====================+
| Session-id     | The socket ID                                                                                                                  | 1..65535            |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Type           | The type of NETCONF session:                                                                                                   | Internal            |
|                | Internal - internal Embedded Event Manager (EEM) session                                                                       | External            |
|                | External - user session                                                                                                        |                     |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| User           | The NETCONF user name                                                                                                          | \-                  |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Group          | NETCONF NACM group name (exist in case NACM admin-state enabled)                                                               | \-                  |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| VRF            | The session management type (in-band or out-of-band)                                                                           | default (in-band)   |
|                |                                                                                                                                | mgmt0 (out-of-band) |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Role           | The role of the user who initiated the NETCONF session                                                                         | Admin               |
|                |                                                                                                                                | Operator            |
|                |                                                                                                                                | Viewer              |
|                |                                                                                                                                | Techsupport         |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Remote Address | The IPv4/IPv6 address and TCP port number of the session initiator. The remote address is relevant to inband connections only. | A.B.C.D:P           |
|                |                                                                                                                                | x:x::x:x:P          |
|                |                                                                                                                                | P = port number     |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Session Uptime | The amount of time that the session has been up                                                                                | X day(s), HH:MM:SS  |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+---------------------+

**Example**
::

    dnRouter# show system netconf sessions

    Netconf Sessions:

    |   Session-ID | Type        | User    | Role     | Group  | VRF         | Remote Address   | Session Uptime   | In rpcs | In bad rpcs | Out rpc errors |
    |--------------+-------------+---------+----------+--------+-------------+------------------+------------------+---------+-------------+----------------|
    |          776 | external    | test    | Admin    | Admin  | default     | 1.1.1.1:2211     | 1 day, 01:01:05  | 200     | 10          | 10             |
    |          806 | external    | test2   | Admin    | Admin  | mgmt0       | 1.2.3.4:32453    | 2 days, 01:01:05 | 33      | 10          | 20             |
    |          805 | external    | test3   | Admin    | Admin  | my_vrf      | 2.2.2.2:2233     | 2 days, 04:02:08 | 10      | 11          | 22             |
    |          846 | internal    | eem_usr | Admin    | Admin  |             |                  | 0 days, 01:01:05 | 10      | 0           | 0              |

.. **Help line:** show active netconf sessions in system.

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 10.0    | Command introduced                                            |
+---------+---------------------------------------------------------------+
| 13.1    | Added OOB support: VRF type (in-band/out-of-band) per session |
+---------+---------------------------------------------------------------+
