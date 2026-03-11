clear services flow-monitoring exporter counters
------------------------------------------------------------

**Minimum user role:** operator

To clear the flow-monitoring cache counters:

**Command syntax: clear services flow-monitoring exporter counters**  ncp [ncp-id] exporter-profile [exporter-profile]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - "clear services flow-monitoring export counters" without parameter, clears counters for exported profiles on all NCPs.


**Parameter table:**

+------------------+--------------------------------------------------------------------------------------+-----------------------------------+-------------+
| Parameter        | Description                                                                          | Range                             |             |
|                  |                                                                                      |                                   | Default     |
+==================+======================================================================================+===================================+=============+
| ncp-id           | Clears the flow-monitoring exporter counters from the specified NCP only             | 0..255                            | \-          |
+------------------+--------------------------------------------------------------------------------------+-----------------------------------+-------------+
| exporter-profile | Clears the flow-monitoring exporter counters for the specified exporter profile only | An existing exporter-profile name | \-          |
+------------------+--------------------------------------------------------------------------------------+-----------------------------------+-------------+

**Example**
::

	dnRouter# clear services flow-monitoring exporter counters ncp 5 

	dnRouter# clear services flow-monitoring exporter counters ncp 5 export-profile myExporter


.. **Help line:** clear counters for exported flows by flow-monitoring.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+