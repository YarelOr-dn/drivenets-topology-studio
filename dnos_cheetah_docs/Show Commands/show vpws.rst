show vpws
---------

**Minimum user role:** viewer

Display the VPWS service status for all VPWS instances. You can filter the output for specific instances using the command parameters:

.. *  insatence - display brief view for service matching instance-name
.. *  interface-name - display brief view for service matching the local AC interface-name
.. *  neighbor - display brief view for services matching neighbor address
.. *  pw-id - display brief view for service matching pw-id
.. *  state - display brief view for service matching state. <Up, Down, Admin-down>

**Command syntax: show vpws** instance [instance-name] interface [interface-name] neighbor [ipv4-address] pw-id [pw-id] state [state]

**Command mode:** operational

**Note**

- When applying multiple filters the output is the combination of all filters.

**Parameter table**

The following information is displayed:

+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter      | Description                                             | Range                                                                                                                                                                                                                                                         | Default |
+================+=========================================================+===============================================================================================================================================================================================================================================================+=========+
| instance-name  | The configured VPWS instance name.                      | string 1..255                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| interface-name | The local interface name.                               | string 1..255                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| ipv4-address   | The neighbors IP address.                               | A.B.C.D                                                                                                                                                                                                                                                       | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| pw-id          | The configured PW-ID.                                   | 1..4294967295                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| state          | The VPWS state. If Down, the down reason is displayed.  | Up, Down, Admin-down.                                                                                                                                                                                                                                         | \-      |
|                |                                                         | Down reasons: local-not-ready, control-word-mismatch ,remote-PSN-port-failure, mtu-mismatch, encap-mismatch, no-mpls-reachability, no-local-AC, local-AC-down, remote-not-ready, remote-AC-down, no-local-AC, local-AC-down, remote-not-ready, remote-AC-down |         |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# show vpws

	| Name            | State    | Time             | Local-IF       | Neighbor      | PW-ID   | Remote-IF      |  PW State                |
	+-----------------+----------+------------------+----------------+---------------+---------+----------------+--------------------------|
	| VPWS_1          | Up       | 0 days, 01:09:57 | bundle-1       | 1.1.1.1       |       1 | ge100-0/0/0    | Up                       |
	| VPWS_2          | Down     | 0 days, 01:23:43 | ge100-1/0/1    | 2.2.2.2       |       2 | bundle-2.2     | encap-mismatch           |

.. **Help line:** show vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
