clear flowspec-local-policies counters
--------------------------------------

**Minimum user role:** operator

To clear FlowSpec counters:

**Command syntax: clear flowspec-local-policies counters** {[address-family] \| [address-family] match-class [match-class-id]}

**Command mode:** operation

.. **Hierarchies**

**Note**

- Optional parameters must match the order in the command.

- When clearing counters for a specific NRLI, destination, or source prefix, you must specify an address-family.

**Parameter table:**


+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| Parameter         | Description                                                                                                                                         | Range               | Default     |
+===================+=====================================================================================================================================================+=====================+=============+
|                   |                                                                                                                                                     |                     |             |
| address-family    | Clears FlowSpec counters only for the specified address-family. When the address-family is not specified, it will apply to   both IPv4 and IPv6.    | IPv4                | both        |
|                   |                                                                                                                                                     |                     |             |
|                   |                                                                                                                                                     | IPv6                |             |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| match-class-id    | Clears counters for a specific match-class                                                                                                          | string              | \-          |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# clear flowspec counters
	dnRouter# clear flowspec counters ipv4
	dnRouter# clear flowspec counters ipv4 match-class mc-1
	dnRouter# clear flowspec counters ipv6
    dnRouter# clear flowspec counters ipv6 match-class mc-3

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 17.0        | Command introduced    |
+-------------+-----------------------+