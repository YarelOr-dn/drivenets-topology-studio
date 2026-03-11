show priority-flow-control interfaces counters
----------------------------------------------

**Minimum user role:** viewer

This command displays PFC counters. If you specify an interface name, the output result is filtered to show only the information for the requested interface.

**Command syntax: show priority-flow-control interfaces counters** [interface-name]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- Physical

..
	**Internal Note**

	- If no interface-name is specified then a summary table is presented for all physical interfaces that PFC is enabled on

**Parameter table**

+----------------+---------------------------------------------------------+---------------------------------+---------+
| Parameter      | Description                                             | Range                           | Default |
+================+=========================================================+=================================+=========+
| interface-name | Optionally filter the counters to a specific interface. | ge<interface speed>-<A>/<B>/<C> | \-      |
+----------------+---------------------------------------------------------+---------------------------------+---------+

The following information is displayed per interface:

+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Attribute               | Description                                                                                                                                     |
+=========================+=================================================================================================================================================+
| Interface               | The name of the interface                                                                                                                       |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Operational             | The state of the link (up/down)                                                                                                                 |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Total RX pause requests | The total number of PFC pause requests received on the interface (a single frame may apply for several traffic classes)                         |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Total TX pause requests | The total number of PFC pause requests transmitted on the interface (a single frame may apply for several traffic classes)                      |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Total RX pause frames   | The total number of PFC pause frames received on the interface                                                                                  |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Total TX pause frames   | The total number of PFC pause frames transmitted on the interface                                                                               |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| CoS                     | The traffic class on the interface that PFC regulates                                                                                           |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| RX pause requests       | The number of PFC pause requests received per traffic class. Each PFC pause frame may contain pause requsets for more than one traffic class    |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| TX pause requests       | The number of PFC pause requests transmitted per traffic class. Each PFC pause frame may contain pause requsets for more than one traffic class |
+-------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+


**Example**
::

	dnRouter# show priority-flow-control interfaces counters

	| Interface    | Operational | Total RX PFC pause requests | Total TX PFC pause requests |
	+--------------+-------------+-----------------------------+-----------------------------|
	| ge100-1/1/1  | up          | 111                         | 222                         |
	| ge100-1/0/21 | up          | 0                           | 0                           |
	| ge100-1/0/22 | up          | 0                           | 0                           |


	dnRouter# show priority-flow-control interfaces counters ge100-1/1/1

	Interface ge100-1/1/1:
	Operational state: up

	Priority Flow Control counters:
		Total RX PFC pause requests:                        111
		Total TX PFC pause requests:                        222
		Total RX PFC frames:                                111
		Total TX PFC frames:                                 88

		| CoS | RX PFC pause requests | TX PFC pause requests |
		+-----+-----------------------+-----------------------|
		| 0   | 111                   | 100                   |
		| 1   | 0                     | 100                   |
		| 2   | 0                     | 0                     |
		| 3   | 0                     | 0                     |
		| 4   | 0                     | 0                     |
		| 5   | 0                     | 0                     |
		| 6   | 0                     | 0                     |
		| 7   | 0                     | 22                    |


.. **Help line:** show priority-flow-control interfaces counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
