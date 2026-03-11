show interfaces breakout
------------------------

**Minimum user role:** viewer

You can use the following command to show information related to interfaces breakout:

**Command syntax: show interfaces breakout** ncp [ncp-id]

**Command mode:** operational



**Note**

- Breakout ports list the ports that are created as a result of setting the breakout mode on the port.

- If ncp-id is specified, only interfaces of the specified NCP are displayed.

**Parameter table**

+-----------+--------+---------------+
| Parameter | Values | Default value |
+===========+========+===============+
| ncp-id    | 0-191  | \-            |
+-----------+--------+---------------+

**Example**
::

	For 10GE interface breakout

	dnRouter# show interfaces breakout

	Sacrificed port is the port that is disabled once the port is in breakout mode.

	+---------------+---------------+-----------------+-------------------------------------------------------------+
	| Port          | Breakout mode | Sacrificed port | Breakup ports                                               |
	+---------------+---------------+-----------------+-------------------------------------------------------------+
	| ge100-0/0/0   | none          | ge100-0/0/21    |                                                             |
	| ge100-0/0/1   | 10g-4x        | ge100-0/0/20    | ge10-0/0/1/0, ge10-0/0/1/1, ge10-0/0/1/2, ge10-0/0/1/3      |
	| ge100-0/0/2   | none          | ge100-0/0/23    |                                                             |
	| ge100-0/0/3   | none          | ge100-0/0/22    |                                                             |
	| ge100-0/0/4   | none          | ge100-0/0/25    |                                                             |
	| ge100-0/0/5   | none          | ge100-0/0/24    |                                                             |
	| ge100-0/0/6   | none          | ge100-0/0/27    |                                                             |
	| ge100-0/0/7   | none          | ge100-0/0/26    |                                                             |
	| ge100-0/0/8   | none          | ge100-0/0/29    |                                                             |
	| ge100-0/0/9   | none          | ge100-0/0/28    |                                                             |
	| ge100-0/0/10  | 10g-4x        | ge100-0/0/31    | ge10-0/0/10/0, ge10-0/0/10/1, ge10-0/0/10/2, ge10-0/0/10/3  |
	| ge100-0/0/11  | none          | ge100-0/0/30    |                                                             |
	| ge100-0/0/12  | none          | ge100-0/0/33    |                                                             |
	| ge100-0/0/13  | none          | ge100-0/0/32    |                                                             |
	| ge100-0/0/14  | none          | ge100-0/0/35    |                                                             |
	| ge100-0/0/15  | none          | ge100-0/0/34    |                                                             |
	| ge100-0/0/16  | none          | ge100-0/0/37    |                                                             |
	| ge100-0/0/17  | none          | ge100-0/0/36    |                                                             |
	| ge100-0/0/18  | none          | ge100-0/0/39    |                                                             |
	| ge100-0/0/19  | none          | ge100-0/0/38    |                                                             |
	| ge100-1/0/1   | none          | ge100-1/0/21    |                                                             |
	| ge100-1/0/2   | none          | ge100-1/0/20    |                                                             |
	| ge100-1/0/3   | none          | ge100-1/0/23    |                                                             |
	| ge100-1/0/4   | none          | ge100-1/0/22    |                                                             |
    +---------------+---------------+-----------------+-------------------------------------------------------------+

	For 400GE interface breakout

	dnRouter# show interfaces breakout

	+---------------+---------------+-----------------+----------------------------------------------------------------+
	| Port          | Breakout mode | Sacrificed port | Breakup ports                                                  |
	+---------------+---------------+-----------------+----------------------------------------------------------------+
	| ge400-0/0/0   | none          |                 |                                                                |
	| ge400-0/0/1   | none          |                 |                                                                |
	| ge400-0/0/2   | 100g-4x       |                 | ge100-0/0/1/0, ge100-0/0/1/1, ge100-0/0/1/2, ge100-0/0/1/3     |
	| ge400-0/0/3   | none          |                 |                                                                |
	| ge400-0/0/4   | none          |                 |                                                                |
	| ...			|				|				  |														     	   |
	| ge400-0/0/9   | none          |                 |                                                                |
	| ge400-0/0/10  | 100g-4x       |                 | ge100-0/0/10/0, ge100-0/0/10/1, ge100-0/0/10/2, ge100-0/0/10/3 |
    +---------------+---------------+-----------------+----------------------------------------------------------------+



.. **Help line:** show interfaces breakout information

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 12.0    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for 400GE breakout |
+---------+----------------------------------+