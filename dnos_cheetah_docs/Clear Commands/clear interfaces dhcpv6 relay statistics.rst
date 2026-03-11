clear interfaces dhcpv6 relay statistics
-----------------------------------------

**Minimum user role:** operator

Clearing the interface DHCPv6 relay statistics resets the counters to zero and removes the counter information from the database.

To clear the interface DHCPv6 relay statistics:

**Command syntax: clear interfaces dhcpv6 relay statistics** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces dhcpv6 relay statistics** - clears DHCPv6 relay counters for **ALL** interfaces.

.. - **Clear interfaces dhcpv6 relay statistics interface-name** - clears DHCPv6 relay counters for the specified interface.

**Parameter table:**

+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------+-------------+
| Parameter         | Description                                                                                                                                            | Range                                             | Default     |
+===================+========================================================================================================================================================+===================================================+=============+
| interface-name    | Clears the DHCPv6 relay counters for the specified interface only. If an interface-name is not specified, the counters are cleared for all interfaces. | ge<interface speed>-<A>/<B>/<C>                   | \-          |
|                   |                                                                                                                                                        | ge<interface speed>-<A>/<B>/<C>.<sub-interface-id>|             |
|                   |                                                                                                                                                        | bundle-<bundle-id>                                |             |
|                   |                                                                                                                                                        | bundle-<bundle-id>.<sub-interface-id>             |             |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear interfaces dhcpv6 relay statistics
	dnRouter# clear interfaces dhcpv6 relay statistics ge100-0/0/0

.. **Help line:** Clear interface DHCPv6 relay counters

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 19.10       | Command introduced    |
+-------------+-----------------------+
