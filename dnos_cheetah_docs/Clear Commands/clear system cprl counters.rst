clear system cprl counters
--------------------------

**Minimum user role:** operator

To clear the CPRL matches and drop counters:

**Command syntax: clear system cprl counters** ncp [ncp]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                  |
+===========+==============================================================================================================================================+
| ncp-id    | Clear the counters for the specified NCP only.If you do not specify an NCP, the CPRL matches and drop counters for all NCPs will be cleared. |
+-----------+----------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# clear system cprl counters ncp 5
	dnRouter# clear system cprl counters


.. **Help line:** clear crpl matches and drop counters

**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 6.0         | Command introduced                          |
+-------------+---------------------------------------------+
|             |                                             |
| 9.0         | Command not supported                       |
+-------------+---------------------------------------------+
|             |                                             |
| 11.0        | Command reintroduced with new NCP filter    |
+-------------+---------------------------------------------+