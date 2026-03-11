clear system upgrade
--------------------

**Minimum user role:** operator

This command removes nodes whose upgrade has failed from the list of "nodes in upgrade" in the show system command output. The failed upgrade state refers to:
•	Firmware-upgrade (failed)
•	BaseOS-upgrade (failed)
To clear system nodes in failed upgrade state:

**Command syntax: clear system upgrade** [serial-number]

**Command mode:** operation

.. **Hierarchies**

**Note**

- Only nodes that are in failed upgrade state can be cleared:
 
  - firmware-upgrade (failed)

  - baseos-upgrade (failed)

If no serial number is specified, all nodes in failed upgrade state will be cleared.

**Parameter table**

+------------------+-----------------------------------------------------------------------------------------------------------------+-----------+-------------+
|                  |                                                                                                                 |           |             |
| Parameter        | Description                                                                                                     | Range     | Default     |
+==================+=================================================================================================================+===========+=============+
|                  |                                                                                                                 |           |             |
| serial-number    | Specify a node's serial-number to remove it from the list. All other nodes (failed or otherwise) remain intact. | \-        | \-          |
|                  |                                                                                                                 |           |             |
|                  | If you do not specify a serial-number, all nodes with a failed upgrade state will be cleared.                   |           |             |
+------------------+-----------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# clear system upgrade ABCDE
	node ABCDE cleared failed state

	dnRouter# clear system upgrade
	node DDDDD cleared failed state
	node BBBBB cleared failed state

	dnRouter# clear system upgrade BBBBB
	Error: node with serial-number BBBBB does not exist!

	dnRouter# clear system upgrade CCCCC
	Error: node with serial-number CCCC is not in upgrade failed state!
	
	dnRouter# clear system upgrade ABCDE
	Error: no nodesin upgrade failed state!



.. **Help line:** clear system nodes in failed upgrade state.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+