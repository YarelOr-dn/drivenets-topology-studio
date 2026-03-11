clear ospf routes
-----------------

**Minimum user role:** operator

The following command clears and re-installs OPSF routes to RIB (for OSPF only - unless fast-reroute is indicated, in order to clear only the LFA routes):

**Command syntax: clear ospf** instance [ospf-instance-name] **routes**

**Command mode:** operation

.. **Hierarchies**

**Note**

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

	dnRouter# clear ospf routes
	dnRouter# clear ospf instance instance1 routes

.. **Help line:** Clear and reinstall OSPF routes

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
