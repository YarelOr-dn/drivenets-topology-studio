clear lldp counters
--------------------

**Minimum user role:** operator

To clear LLDP counters:

**Command syntax: clear lldp counters [interface-name]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - **Clear lldp counters** - clears all counters for **all** interfaces/sessions

 - **Clear lldp counters interface x** - clears all counters for a specific interface


**Parameter table:**

+-------------------+---------------------------------------------------------------+---------------------------------+-------------+
|                   |                                                               |                                 |             |
| Parameter         | Description                                                   | Range                           | Default     |
+===================+===============================================================+=================================+=============+
|                   |                                                               |                                 |             |
| interface-name    | Clears the LLDP counters only for the specified interface.    | Physical interfaces:            | \-          |
|                   |                                                               |                                 |             |
|                   |                                                               | ge<interface speed>-<A>/<B>/<C> |             |
|                   |                                                               |                                 |             |
|                   |                                                               | ncp-<X>.mgmt<Y>                 |             |
|                   |                                                               |                                 |             |
|                   |                                                               | ncf-<X>.mgmt<Y>                 |             |
|                   |                                                               |                                 |             |
|                   |                                                               | ncc-<X>.mgmt<Y>                 |             |
+-------------------+---------------------------------------------------------------+---------------------------------+-------------+


**Example**
::

	dnRouter# clear lldp counters
	dnRouter# clear lldp counters ge100-2/1/1
	dnRouter# clear lldp counters ge100-4/1/2


.. **Help line:** clear lldp counters

**Command History**

+-------------+----------------------------------+
|             |                                  |
| Release     | Modification                     |
+=============+==================================+
|             |                                  |
| 7.0         | Command introduced               |
+-------------+----------------------------------+
|             |                                  |
| 9.0         | Not supported in this version    |
+-------------+----------------------------------+
|             |                                  |
| 10.0        | Command reintroduced             |
+-------------+----------------------------------+