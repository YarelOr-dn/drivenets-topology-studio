clear interfaces management counters
------------------------------------

**Minimum user role:** operator

To clear counter information relating to management interfaces:

**Command syntax: clear interfaces management counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces management counters** - clears all counters for **ALL** interfaces

.. - **Clear interfaces management counters interface x** - clears all counters for a specific interface.


**Parameter table:**

+-------------------+-----------------------------------------------------------------+-----------+-------------+
|                   |                                                                 |           |             |
| Parameter         | Description                                                     | Range     | Default     |
+===================+=================================================================+===========+=============+
|                   |                                                                 | String    | \-          |
| interface-name    | Clears counter information from the specified interface only    |           |             |
+-------------------+-----------------------------------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# clear interfaces management counters
	dnRouter# clear interfaces management counters mgmt0
	dnRouter# clear interfaces management counters mgmt-ncc-0



.. **Help line:** clear control interface counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+