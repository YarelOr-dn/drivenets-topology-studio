clear system npu-resources counters
-----------------------------------

**Minimum user role:** operator

Clear system NPU resources counters.

**Command syntax: clear system npu-resources counters** resource-type [resource-type] ncp [ncp-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

- If ncp-id is specified, only the system NPU resources counters of the NCP with specified id are cleared. Otherwise system resources counters of all NCPs are cleared.

- If resource-type is specified, only the system NPU resources counters for the specified resource type are cleared. For resources that are per NCP, if ncp-id is also specified, then only the applicable counters are cleared.


**Parameter table**

+---------------+---------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------+
| Parameter     | Description                                                                                                                           | Range                                    |
+===============+=======================================================================================================================================+==========================================+
| ncp-id        | Clear the counters for the specified NCP only. If you do not specify an NCP, the NPU resources counters for all NCPs will be cleared. | 0..max number of NCP per cluster type -1 |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------+
| resource-type | Clear the counters for the specified resource only.                                                                                   | shared-buffer                            |
|               |                                                                                                                                       | mtu-profiles                             |
|               |                                                                                                                                       | traffic-utilization                      |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------+


**Example**
::

	dnRouter# clear system npu-resources counters
	dnRouter# clear system npu-resources counters ncp 1
	dnRouter# clear system npu-resources counters resource-type flowspec
	dnRouter# clear system npu-resources counters ncp 2 resource-type shared-buffer


.. **Help line:** clear system NPU resources counters

**Command History**

+-------------+-------------------------------------------------------------------+
| Release     | Modification                                                      |
+=============+===================================================================+
| 11.4        | Command introduced                                                |
+-------------+-------------------------------------------------------------------+
| 19.1        | Command renamed and additional filter per resource-type was added |
+-------------+-------------------------------------------------------------------+