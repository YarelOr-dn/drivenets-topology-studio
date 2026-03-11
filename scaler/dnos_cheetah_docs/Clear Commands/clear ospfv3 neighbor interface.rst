clear ospfv3 neighbor interfaces
--------------------------------

**Minimum user role:** operator

To clear OSPFv3 interface information:

**Command syntax: clear ospfv3 neighbor interface** [interface-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

- add *interface-name* to clear information for a specific interface


**Parameter table:**

**Parameter table:**

+-------------------+--------------------------------------------------------------+---------------------------------------+-------------+
|                   |                                                              |                                       |             |
| Parameter         | Description                                                  | Range                                 | Default     |
+===================+==============================================================+=======================================+=============+
|                   |                                                              |                                       |             |
| interface-name    | clears the ospf information for the specified interface      | configured interface name.            | \-          |
|                   |                                                              |                                       |             |
|                   |                                                              | ge{/10/25/40/100}-X/Y/Z               |             |
|                   |                                                              |                                       |             |
|                   |                                                              | bundle-<bundle id>                    |             |
|                   |                                                              |                                       |             |
|                   |                                                              | bundle-<bundle id>.<sub-interface id> |             |
|                   |                                                              |                                       |             |
|                   |                                                              |                                       |             |
+-------------------+--------------------------------------------------------------+---------------------------------------+-------------+


**Example**
::

	dnRouter# clear ospfv3 neighbor interface
	dnRouter# clear ospfv3 neighbor interfaces bundle-2.2004

.. **Help line:** Clear OSPFv3 neighbor interface information


**Command History**

+-------------+------------------------------------------------------------------+
|             |                                                                  |
| Release     | Modification                                                     |
+=============+==================================================================+
|             |                                                                  |
| 6.0         | Command introduced                                               |
+-------------+------------------------------------------------------------------+
|             |                                                                  |
| 11.6        | Renamed to 'ospfv3 neighbor interfaces' and introduced OSPFv3    |
+-------------+------------------------------------------------------------------+