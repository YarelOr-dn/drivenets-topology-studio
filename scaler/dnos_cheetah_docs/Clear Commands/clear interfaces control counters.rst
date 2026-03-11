clear interfaces control counters
---------------------------------

**Minimum user role:** operator

To clear counter information relating to control interfaces:

**Command syntax: clear interfaces control counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces dampening** - clears all counters for **ALL** interfaces

.. - **Clear interfaces dampening interface x** - clears **ALL** counters for a specific interface.

**Parameter table:**

+-------------------+-----------------------------------------------------------------+------------------+-------------+
|                   |                                                                 |                  |             |
| Parameter         | Description                                                     | Range            | Default     |
+===================+=================================================================+==================+=============+
|                   |                                                                 |                  | \-          |
| interface-name    | Clears counter information from the specified interface only    | ctrl-ncf-x/y     |             |
|                   |                                                                 |                  |             |
|                   |                                                                 | ctrl-ncp-x/y     |             |
|                   |                                                                 |                  |             |
|                   |                                                                 | ctrl-ncc-x/y     |             |
|                   |                                                                 |                  |             |
|                   |                                                                 | ctrl-ncm-Ax/y    |             |
|                   |                                                                 |                  |             |
|                   |                                                                 | ctrl-ncm-Bx/y    |             |
+-------------------+-----------------------------------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# clear interfaces control counters
	dnRouter# clear interfaces control counters ctrl-ncf-0/0


.. **Help line:** clear control interface counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+