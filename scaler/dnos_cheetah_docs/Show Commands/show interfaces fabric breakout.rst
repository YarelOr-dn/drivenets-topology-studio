show interfaces fabric breakout
-------------------------------

**Minimum user role:** viewer

You can use the following command to show information related to fabric interfaces breakout:

**Command syntax: show interfaces breakout** {ncp [ncp-id] \| ncf [ncf-id]} **

**Command mode:** operational



**Note**

- Breakout ports list the ports that are created as a result of setting the breakout mode on the port.

- If node id is specified, only interfaces of the specified NCP or NCF node are displayed.

**Parameter table**

+-----------+--------+---------------+
| Parameter | Values | Default value |
+===========+========+===============+
| ncp-id    | 0-255  | \-            |
| ncf-id    | 0-35   | \-            |
+-----------+--------+---------------+

**Example**
::

	For 800GE interface breakout on NCP-18E

	dnRouter# show interfaces fabric breakout
	or
	dnRouter# show interfaces fabric breakout ncp 0

	+------------------------+---------------+-----------------+----------------------------------------------------------------+
	| Port                   | Breakout mode | Sacrificed port | Breakup ports                                                  |
	+------------------------+---------------+-----------------+----------------------------------------------------------------+
	| fab-ncp-800-0/0/0      | 400g-2x       |                 | fab-ncp-400-0/0/0/0, fab-ncp-400-0/0/0/1                       |
	| fab-ncp-800-0/0/1      | 400g-2x       |                 | fab-ncp-400-0/0/1/0, fab-ncp-400-0/0/1/1                       |
	| fab-ncp-800-0/0/2      | 400g-2x       |                 | fab-ncp-400-0/0/2/0, fab-ncp-400-0/0/2/1                       |
	| ....                   |               |                 |                                                                |
	| fab-ncp-800-0/0/17     | 400g-2x       |                 | fab-ncp-400-0/0/17/0, fab-ncp-400-0/0/17/1                     |
	+------------------------+---------------+-----------------+----------------------------------------------------------------+

**Example**
::

	For 800GE interface breakout on NCF-128E

	dnRouter# show interfaces fabric breakout
	or
	dnRouter# show interfaces fabric breakout ncf 1

	+------------------------+---------------+-----------------+----------------------------------------------------------------+
	| Port                   | Breakout mode | Sacrificed port | Breakup ports                                                  |
	+------------------------+---------------+-----------------+----------------------------------------------------------------+
	| fab-ncf-800-1/0/0      | 400g-2x       |                 | fab-ncf-400-1/0/0/0, fab-ncf-400-1/0/0/1                       |
	| fab-ncf-800-1/0/1      | 400g-2x       |                 | fab-ncf-400-1/0/1/0, fab-ncf-400-1/0/1/1                       |
	| fab-ncf-800-1/0/2      | 400g-2x       |                 | fab-ncf-400-1/0/2/0, fab-ncf-400-1/0/2/1                       |
	| ....                   |               |                 |                                                                |
	| fab-ncf-800-1/7/15     | 400g-2x       |                 | fab-ncf-400-1/7/15/0, fab-ncf-400-1/7/15/1                     |
	+------------------------+---------------+-----------------+----------------------------------------------------------------+


.. **Help line:** show interfaces fabric breakout information

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 19.10   | Command introduced               |
+---------+----------------------------------+