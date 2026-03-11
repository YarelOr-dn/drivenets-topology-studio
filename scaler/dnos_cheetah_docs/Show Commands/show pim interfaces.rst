show pim interfaces
-------------------

**Minimum user role:** viewer

You can use this command to display PIM interface information.

**Command syntax: show pim interfaces** [interface-name]

**Command mode:** operational



.. **Note**

	- Only PIM enabled interfaces are shown.

	- Boundary policy: If defined the Prefix list name is displayed, else 'none' indicate no boundary policy definition.

**Parameter table**

+----------------+-------------------------------+------------------------------------------------------+---------+
| Parameter      | Description                   | Range                                                | Default |
+================+===============================+======================================================+=========+
| interface-name | The name of the PIM interface | ge<interface speed>-<A>/<B>/<C>[.<sub-interface id>] | none    |
|                |                               | bundle-<bundle id>[.<sub-interface id>]              |         |
|                |                               | lo<lo-interface id>                                  |         |
+----------------+-------------------------------+------------------------------------------------------+---------+

The following are the arguments for this command:

+--------------------+---------------------------------------------------------------------+
| Parameter          | Description                                                         |
+====================+=====================================================================+
| Interface          | The Interface on which PIM is enabled                               |
+--------------------+---------------------------------------------------------------------+
| IP Address         | Interface IP address                                                |
+--------------------+---------------------------------------------------------------------+
| PIM admin state    | The PIM admin status of the interface                               |
+--------------------+---------------------------------------------------------------------+
| If. oper. state    | The operational status of the interface                             |
+--------------------+---------------------------------------------------------------------+
| Nbr Count          | Number of PIM peer neighbors on the interface                       |
+--------------------+---------------------------------------------------------------------+
| Hello Interval     | The configured PIM hello interval on the related interface          |
+--------------------+---------------------------------------------------------------------+
| Join Count ( \*, G)| Number of PIM ( \*,G) join states sent to PIM peers on the interface|
+--------------------+---------------------------------------------------------------------+
| Join Count ( S, G) | Number of PIM (S,G) join states sent to PIM peers on the interface  |
+--------------------+---------------------------------------------------------------------+
| DR address         | The IP address of the selected DR PIM router                        |
+--------------------+---------------------------------------------------------------------+
| Boundary policy    | The Boundary policy prefix list                                     |
+--------------------+---------------------------------------------------------------------+

**Example**
::

	dnRouter# show pim interfaces

	PIM interfaces in VRF: default
	+-----------------------------+-----------------+-------------+-------------+-------+----------+--------+--------+
	| Interface                   | IP address      | PIM         | Interface   | Nbr   | Hello    | Join   | Join   |
	|                             |                 | Admin state | Oper state  | count | interval | (*,G)  | (S,G)  |
	+-----------------------------+-----------------+-------------+-------------+-------+----------+--------+--------+
	| bundle-2.100                | 12.5.6.1        | enabled     | up          | 1     | 30       | 4      | 2      |
	| bundle-3.200                | 12.1.3.2        | enabled     | up          | 1     | 30       | 2      | 12     |
	| bundle-20.222               | 12.2.7.2        | enabled     | up          | 1     | 30       | 1      | 32     |
	| Lo0                         | 2.2.2.2         | enabled     | up          | 0     | N/A      | 0      | 0      |
	| ge100-1/2/1                 | 12.12.7.1       | enabled     | up          | 1     | 30       | 0      | 12     |
	| ge100-1/0/0.1               | 11.2.62.1       | enabled     | up          | 1     | 30       | 12     | 6      |
	| ge100-1/3/12.201            | 110.122.128.101 | enabled     | down        | 0     | 30       | 0      | 0      |
	+-----------------------------+-----------------+-------------+-------------+-------+----------+--------+--------+


	dnRouter# show pim interfaces bundle-20.222

	PIM interfaces in VRF: default

	Interface: bundle-20.222
		IP address: 12.2.7.2
		PIM admin state: enabled
		Interface operational state: up
		DR Address: 12.2.7.2
		PIM Neighbor Count: 1
		Hello Interval: 30 Seconds
		Join Count (*,G): 12
		Join Count (S,G): 32
		Boundary policy: BOUNDARY_LOCAL_MC_POL


	dnRouter# show pim interfaces bundle-2.100

	PIM interfaces in VRF: default

 	Interface: bundle-2.100
		IP address: 12.5.6.1
		PIM admin state: enabled
		Interface operational state: up
		DR Address: 12.2.6.1
		PIM Neighbor Count: 1
		Hello Interval: 30 Seconds
		Join Count (*,G): 12
		Join Count (S,G): 32
		Boundary policy: none

.. **Help line:** Show PIM interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
