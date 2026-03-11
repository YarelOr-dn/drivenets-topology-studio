clear ospf neighbor interface
-----------------------------

**Minimum user role:** operator

To clear the entire OSPF interface information:

**Command syntax: clear ospf** instance [ospf-instance-name] **neighbor interface** [interface-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

- add *interface-name* to clear information for a specific interface

- use "instance [ospf-instance-name]" to clear information from a specific OSPF instance, when not specified, clear information from all OSPF instances

**Parameter table:**

+--------------------+----------------------------------------------------------------+---------------------------------------+-------------+
|                    |                                                                |                                       |             |
| Parameter          | Description                                                    | Range                                 | Default     |
+====================+================================================================+=======================================+=============+
|                    |                                                                |                                       |             |
| interface-name     | clears the ospf information for the specified interface        | configured interface name.            | \-          |
|                    |                                                                |                                       |             |
|                    |                                                                | ge{/10/25/40/100}-X/Y/Z               |             |
|                    |                                                                |                                       |             |
|                    |                                                                | bundle-<bundle id>                    |             |
|                    |                                                                |                                       |             |
|                    |                                                                | bundle-<bundle id>.<sub-interface id> |             |
|                    |                                                                |                                       |             |
|                    |                                                                |                                       |             |
+--------------------+----------------------------------------------------------------+---------------------------------------+-------------+
| ospf-instance-name | clears the ospf information for the specified instance         | configured instances names            | all         |
+--------------------+----------------------------------------------------------------+---------------------------------------+-------------+


**Example**
::

	dnRouter# clear ospf neighbor interface
	dnRouter# clear ospf instance instance1 neighbor interface
	dnRouter# clear ospf neighbor interface bundle-2.2004
	dnRouter# clear ospf instance instance1 neighbor interface bundle-2.2004


.. **Help line:** Clear OSPF neighbor interfaces information.

**Command History**

+-------------+------------------------------------------------------------------+
|             |                                                                  |
| Release     | Modification                                                     |
+=============+==================================================================+
|             |                                                                  |
| 6.0         | Command introduced                                               |
+-------------+------------------------------------------------------------------+
|             |                                                                  |
| 11.6        | Renamed to 'ospf neighbor interfaces'                            |
+-------------+------------------------------------------------------------------+
| 18.2        | Add instance parameter                                           |
+-------------+------------------------------------------------------------------+
