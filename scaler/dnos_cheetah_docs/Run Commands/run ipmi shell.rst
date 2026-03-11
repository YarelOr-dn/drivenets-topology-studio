run ipmi shell
--------------

**Minimum user role:** admin

To access the HostOS shell of an relevant element/node via the IPMI interface:

**Command syntax: run ipmi shell [node-name] [node-id]**

**Command mode:** operation

.. **Note**

	- "exit" commands reverts back to the DNOS CLI.

**Parameter table**

+-----------+-------------------------------------------------------------+-----------------------------------------------+
| Parameter | Description                                                 | Range                                         |
+===========+=============================================================+===============================================+
| node-name | Specify the node to which you want access to the ipmi shell | NCP                                           |
|           |                                                             | NCF                                           |
|           |                                                             | NCM                                           |
+-----------+-------------------------------------------------------------+-----------------------------------------------+
| node-id   | Specify the ID of the node you want to access               | NCC - 0..1                                    |
|           |                                                             | NCP - 0..(max NCP number per cluster type -1) |
|           |                                                             | NCF - 0..(max NCF number per cluster type -1) |
|           |                                                             | NCM - a0, b0, a1, b1                          |
+-----------+-------------------------------------------------------------+-----------------------------------------------+

**Example**
::

	dnRouter# run ipmi shell ncp 1
	root@wb12315812:/#

	root@wb12315812:/# exit
	dnRouter#

	dnRouter# run ipmi shell ncf 1
	root@wb12315812:/#

	root@wb12315812:/# exit
	dnRouter#

	dnRouter# run ipmi shell ncm a0
	root@wb12315812:/#

	root@wb12315812:/# exit
	dnRouter#

.. **Help line:** access to shell of the NCP/NCF/NCM components

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 11.6    | Removed option to access the NCC |
+---------+----------------------------------+


