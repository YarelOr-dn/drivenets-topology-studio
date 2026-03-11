clear qppb counters
-------------------

**Minimum user role:** operator

To clear the QPPB counters, use the following command:

**Command syntax: clear qppb counters** interface [interface-name] rule-id [rule-id]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - **Clear qppb counters** - if no interface clears all QPPB counters on all interfaces

 - **Clear qppb counters interface x** - clears all QPPB counters on the specified interface

 - **Clear qppb counters** - if no rule-id is given, clears all QPPB counters on all rules

 - **Clear qppb counters rule-id x** - clears all QPPB counters of the specified rule-id

**Parameter table:**

+----------------+-------------------------------------------------------------------------------+---------------------------------+---------+
| Parameter      | Description                                                                   | Range                           | Default |
+================+===============================================================================+=================================+=========+
| interface-name | Clears the QPPB counters from the specified interface only.                   | ge<interface speed>-<A>/<B>/<C> | \-      |
|                | If you do not specify an [interface-name], all QPPB counters will be cleared. |                                 |         |
|                |                                                                               |                                 |         |
+----------------+-------------------------------------------------------------------------------+---------------------------------+---------+
| rule-id        | Clears the QPPB counters of the specified rule only.                          | 1..128                          | \-      |
|                | If you do not specify a rule-id, all QPPB counters will be cleared.           |                                 |         |
|                |                                                                               |                                 |         |
+----------------+-------------------------------------------------------------------------------+---------------------------------+---------+


**Example**
::

	dnRouter# clear qppb counters
	dnRouter# clear qppb counters interface ge100-1/1/1
	dnRouter# clear qppb counters interface bundle-1
    dnRouter# clear qppb counters interface ge100-1/1/1 rule-id 10
	dnRouter# clear qppb counters rule-id 30


.. **Help line:** clear qppb counters attached to interface

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 17.1    | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+