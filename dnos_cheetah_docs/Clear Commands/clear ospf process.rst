clear ospf process
------------------

**Minimum user role:** operator

To clear the entire OSPF database and restart the adjacencies:

**Command syntax: clear ospf** instance [ospf-instance-name] **process**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

	- use "instance [ospf-instance-name]" to clear information from a specific OSPF instance, when not specified, clear information from all OSPF instances

**Parameter table:**

+--------------------+----------------------------------------------------------------+---------------------------------------+-------------+
|                    |                                                                |                                       |             |
| Parameter          | Description                                                    | Range                                 | Default     |
+====================+================================================================+=======================================+=============+
| ospf-instance-name | clears the ospf information for the specified instance         | configured instances names            | all         |
+--------------------+----------------------------------------------------------------+---------------------------------------+-------------+

**Example**
::

	dnRouter# clear ospf process
	dnRouter# clear ospf instance instance1 process

.. **Help line:** Clear OSPF process

**Command History**

+-------------+------------------------+
|             |                        |
| Release     | Modification           |
+=============+========================+
|             |                        |
| 11.6        | Command introduced     |
+-------------+------------------------+
| 18.2        | Add instance parameter |
+-------------+------------------------+
