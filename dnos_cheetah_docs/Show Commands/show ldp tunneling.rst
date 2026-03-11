show ldp tunneling
-------------------

**Minimum user role:** viewer

To display information on LDP tunneling over RSVP tunnels:



**Command syntax: show ldp tunneling**

**Command mode:** operational



**Note**

- ldp-shortcuts-sync state can be one of the following:

	- up - Session is up. LDP on-session-delay expired IGP Shortcuts uses the rsvp/sr-te tunnel.

	- down - Session is Down IGP Shortcuts does not use the rsvp/sr-te tunnel.


**Example**
::

	dnRouter# show ldp tunneling

	| Destination | Hello Timers | LDP Peer ID (uptime)       | ldp-sync                 | RSVP/SR-TE Tunnel Name |
	+=============+==============+============================+==========================+========================+
	| 9.9.9.9     | 10/90        | 9.9.9.9:0 (5 days 06:31:22)|  up                      | TUNNEL_1               |
	| 9.9.9.9     | 10/90        | 9.9.9.9:0 (00:01:54)       |  down                    | TUNNEL_2               |
	| 9.9.9.9     | 10/90        | 9.9.9.9:0 (5 days 06:31:22)|  up                      | POLICY_1               |
	| 9.9.9.9     | 10/90        | 9.9.9.9:0 (00:01:54)       |  down                    | POLICY_2               |
	| 1.1.1.1     | 10/90        | 0.0.0.0:0 (00:00:00)       |  up                      | TUNNEL_3               |
	| 2.2.2.2     | 10/90        | 2.2.2.2:0 (1 days 09:34:54)|  up                      | TUNNEL_4               |

.. **Help line:** Displays information about LDP tunneling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+


