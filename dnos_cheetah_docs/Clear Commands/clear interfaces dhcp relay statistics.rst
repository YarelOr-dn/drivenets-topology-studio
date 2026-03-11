clear interfaces dhcp relay statistics
--------------------------------------

**Minimum user role:** operator

Clearing the interface DHCP relay statistics resets the counters to zero and removes the counter information from the database.

To clear the interface DHCP relay statistics:

**Command syntax: clear interfaces dhcp relay statistics** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces dhcp relay statistics** - clears DHCP relay counters for **ALL** interfaces.

.. - **Clear interfaces dhcp relay statistics interface-name** - clears DHCP relay counters for the specified interface.

**Parameter table:**

+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------+-------------+
| Parameter         | Description                                                                                                                                            | Range                                             | Default     |
+===================+========================================================================================================================================================+===================================================+=============+
| interface-name    | Clears the DHCP relay counters for the specified interface only. If an interface-name is not specified, the counters are cleared for all interfaces.   | ge<interface speed>-<A>/<B>/<C>                   | \-          |
|                   |                                                                                                                                                        | ge<interface speed>-<A>/<B>/<C>.<sub-interface-id>|             |
|                   |                                                                                                                                                        | bundle-<bundle-id>                                |             |
|                   |                                                                                                                                                        | bundle-<bundle-id>.<sub-interface-id>             |             |
|                   |                                                                                                                                                        | irbX                                              |             |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear interfaces dhcp relay statistics
	dnRouter# clear interfaces dhcp relay statistics ge100-0/0/0

.. **Help line:** Clear interface DHCP relay counters

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 18.0        | Command introduced    |
+-------------+-----------------------+
