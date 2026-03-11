show prefix-list 
-----------------

**Minimum user role:** viewer

To display a prefix-list:



**Command syntax: show prefix-list [address-family] [protocol]** detail \| summary [prefix-list-name] {prefix [ip-prefix] \| rule-id [rule-id] }

**Command mode:** operational



**Note**

- The vertical bar (|) indicates that only one of the parameters can appear in the command.

.. - detail is optional, when specified displays detailed information

	- summary is optional, when specified displays prefix-lists summary

	- prefix, rule-id can only be set with a specific prefix-list name (with no detail and summary option) - displays information for the specified ip-prefix or rule-id from the prefix-list

**Parameter table**

+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| Parameter        | Description                                                                                                      | Range          | Default |
+==================+==================================================================================================================+================+=========+
| address-family   | The IPv4 or IPv6 address family                                                                                  | IPv4           | \-      |
|                  |                                                                                                                  | IPv6           |         |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| protocol         | The protocol for which to display the prefix-list                                                                | BGP            | \-      |
|                  |                                                                                                                  | OSPF           |         |
|                  |                                                                                                                  | RIB-manager    |         |
|                  |                                                                                                                  | RSVP           |         |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| detail           | Display detailed information                                                                                     | \-             | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| summary          | Display a prefix-list summary                                                                                    | \-             | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| prefix-list-name | Optionally filter the information to a specific prefix-list. When not specified, all prefix-lists are displayed. | String         | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| ip-prefix        | Optionally filters the information to a specific ip-prefix from the prefix-list                                  | A.B.C.D/x      | \-      |
|                  |                                                                                                                  | xx:xx::xx:xx/x |         |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+
| rule-id          | Optionally filters the information to a specific rule-id from the prefix-list                                    | 1..65534       | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------+----------------+---------+

**Example**
::

	dnRouter# show prefix-list ipv6 bgp
	dnRouter# show prefix-list ipv4 ospf PL_NAME
	dnRouter# show prefix-list ipv4 rib-manager summary
	dnRouter# show prefix-list ipv4 bgp detail PL_NAME
	dnRouter# show prefix-list ipv4 bgp PL_NAME prefix 2.2.0.0/24
	dnRouter# show prefix-list ipv4 bgp PL_NAME rule-id 10

.. **Help line:** Displays a prefix-list

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 6.0     | Command introduced                    |
+---------+---------------------------------------+
| 11.2    | Added RSVP to the protocols parameter |
+---------+---------------------------------------+

