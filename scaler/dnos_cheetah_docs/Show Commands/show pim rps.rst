show pim rps
------------

**Minimum user role:** viewer

You can use this command to display the actual PIM entries RPF checks results. The table incorporates successful and failed RPF(s) or RPF(RP) checks.



**Command syntax: show pim rps**

**Command mode:** operational



**Note**

- The "Failed RPF" flag indicates that the IIF currently installed in the FIB for the given state has failed the RPF check.

.. - When RP Address is local a "(Local RP)" indication is printed in the RPF field.


**Parameter table**

+-----------+------------------------------------------------------------------------------------------------+-------------------------------------------------------------+---------+
| Parameter | Description                                                                                    | Range                                                       | Default |
+===========+================================================================================================+=============================================================+=========+
| group     | The group IP address for which all relevant (\*,G) and (S,G) PIM RPF entries will be displayed | Group IPv4 address (only IPv4 family address is supported)  | \-      |
+-----------+------------------------------------------------------------------------------------------------+-------------------------------------------------------------+---------+
| source    | The source IP address for which all relevant (\*,G) and (S,G) PIM RPF entries will be displayed| Source IPv4 address (only IPv4 family address is supported) | \-      |
+-----------+------------------------------------------------------------------------------------------------+-------------------------------------------------------------+---------+

**Example**
::

  dnRouter# show pim rps

	PIM RP List vrf: default
	+----------------------------+------------+-------------+-------------+-----------------------------------------------+
	| RP Address                 | RP Type    | RPF(RP)     | Holdtime    | Group Prefix-List                             |
	+----------------------------+------------+-------------+-------------+-----------------------------------------------+
	| 2.2.2.2                    | static     | 12.1.3.1    |    N/A      | RP-2222-GROUP-MAPPING                         |
	| 5.5.5.5                    | static     | 12.1.2.2    |    N/A      | RP-5555-GROUP-MAPPING                         |
	| 6.6.6.6                    | static     | 12.61.62.1  |    N/A      | RP-6666-GROUP-MAPPING                         |
	| 61.61.61.61                | static     | (local RP)  |    N/A      | RP-61616161-GROUP-MAPPING                     |
	+----------------------------+------------+-------------+-------------+-----------------------------------------------+

.. **Help line:** Show PIM Rendezvous Point Routers information

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 12.0    | Command introduced                                 |
+---------+----------------------------------------------------+
| 13.0    | Updated command syntax to support group and source |
+---------+----------------------------------------------------+
| 13.3    | Added the 'Failed RPF' flag in the command output  |
+---------+----------------------------------------------------+
