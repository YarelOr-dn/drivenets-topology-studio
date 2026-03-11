show pim rpf
------------

**Minimum user role:** viewer

You can use this command to display the actual PIM entries RPF checks results. The table incorporates successful and failed RPF(s) or RPF(RP) checks.



**Command syntax:show pim rpf** group [group] source [source]

**Command mode:** operational



**Note**

- The "Failed RPF" flag indicates that the IIF currently installed in the FIB for the given state has failed the RPF check.

.. - With no parameter all the PIM RPF entries will be displayed.

	- In case only Group address is provided than all relevant ( ``*``,G) and (S,G) PIM RPF entries with same Group will be displayed.

	- When both Group and Source are provided the PIM RPF of the (S,G) entry is displayed.

	- The 'Failed RPF' flag indicates that the IIF currently installed in FIB for the given state has failed RPF check.

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

	dnRouter# show pim rpf

	Legend: F - Failed RPF

	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| Source            | Group              | RPF Interface        | RPF address       | RIB Next Hop       | Metric  | Distance |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| *                 | 239.1.1.1          | lo1                  | *                 | 13.13.13.12        | 0       | 0        |
	| 101.1.1.1         | 239.1.1.1          | bundle-3.1221        | 192.168.10.1      | 192.168.10.1       | 0       | 0        |
	| 101.2.2.2         | 239.1.1.1          | bundle-32.521        | 10.2.1.54         | 10.2.1.54          | 0       | 0        |
	| 191.1.2.34        | 239.10.0.0         | bundle-1.2003 (F)    | 192.168.0.1       | 192.168.0.1        | 0       | 0        |
	| 192.1.2.3         | 239.10.0.0         | bundle-12.876        | 192.168.0.3       | 192.168.0.1        | 0       | 0        |
	| *                 | 239.10.0.0         | lo1                  | *                 | 13.13.13.12        | 0       | 0        |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+


	dnRouter# show pim rpf group 239.1.1.1

	Legend: F - Failed RPF

	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| Source            | Group              | RPF Interface        | RPF address       | RIB Next Hop       | Metric  | Distance |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| *                 | 239.1.1.1          | lo1                  | *                 | 13.13.13.12        | 0       | 0        |
	| 101.1.1.1         | 239.1.1.1          | bundle-3.1221        | 192.168.10.1      | 192.168.10.1       | 0       | 0        |
	| 101.2.2.2         | 239.1.1.1          | bundle-32.521        | 10.2.1.54         | 10.2.1.54          | 0       | 0        |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+


	dnRouter# show pim rpf group 239.1.1.1 source 101.2.2.2

	Legend: F - Failed RPF

	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| Source            | Group              | RPF Interface        | RPF address       | RIB Next Hop       | Metric  | Distance |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+
	| 101.2.2.2         | 239.1.1.1          | bundle-32.521        | 10.2.1.54         | 10.2.1.54          | 0       | 0        |
	+-------------------+--------------------+----------------------+-------------------+--------------------+---------+----------+

.. **Help line:** Displays the actual PIM entries rpf check results.

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
