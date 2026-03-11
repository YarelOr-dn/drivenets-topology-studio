clear priority-flow-control counters
------------------------------------

**Minimum user role:** operator

To clear the PFC counters, use the following command:

**Command syntax: clear priority-flow-control counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - **clear priority-flow-control counters** - clears all PFC counters on all interfaces

 - **clear priority-flow-control counters interface x** - clears all PFC counters on the specified interface

**Parameter table:**

+----------------+------------------------------------------------------------------------------+---------------------------------+---------+
| Parameter      | Description                                                                  | Range                           | Default |
+================+==============================================================================+=================================+=========+
| interface-name | Clears the PFC counters from the specified interface only.                   | ge<interface speed>-<A>/<B>/<C> | \-      |
|                | If you do not specify an [interface-name], all PFC counters will be cleared. |                                 |         |
|                |                                                                              | bundle-<bundle-id>              |         |
+----------------+------------------------------------------------------------------------------+---------------------------------+---------+


**Example**
::

	dnRouter# clear priority-flow-control counters
	dnRouter# clear priority-flow-control counters ge100-1/1/1
	dnRouter# clear priority-flow-control counters ge100-0/0/0/1


.. **Help line:** clear priority-flow-control counters

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 17.0    | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+