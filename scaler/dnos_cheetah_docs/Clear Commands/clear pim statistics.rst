clear pim statistics
--------------------

**Minimum user role:** operator

You can use the command to clear PIM statistics for all interfaces. You can clear the PIM statistics for a specific interface using the [interface-name] command.

**Command syntax: clear pim statistics** interface [interface-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

- If the interface is indicated then only the specified interface PIM statistics are cleared.

**Parameter table:**

+-------------------+----------------------------------------------------------------+-----------------------------------------+-------------+
|                   |                                                                |                                         |             |
| Parameter         | Description                                                    | Range                                   | Default     |
+===================+================================================================+=========================================+=============+
|                   |                                                                |                                         |             |
| interface-name    | Clears the statistics for a specific interface (or for all)    | ge{/10/25/40/100}-X/Y/Z                 | none        |
|                   |                                                                |                                         |             |
|                   |                                                                | bundle<bundle-id>                       |             |
|                   |                                                                |                                         |             |
|                   |                                                                | bundle<bundle-id>.<sub-interface-id>    |             |
+-------------------+----------------------------------------------------------------+-----------------------------------------+-------------+

**Example**
::

  dnRouter# clear pim statistics
  dnRouter# clear pim statistics interface bundle-20.222

.. **Help line:** Clear PIM statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+