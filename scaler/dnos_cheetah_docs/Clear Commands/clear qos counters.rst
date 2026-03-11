clear qos counters
------------------

**Minimum user role:** operator

To clear the QoS counters, use the following command:

**Command syntax: clear qos counters** [interface-name] [direction]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - **Clear qos counters** - clears all QoS counters (including egress-queues stats) on all interfaces

 - **Clear qos counters interface x** - clears all QoS counters on the specified interface

**Parameter table:**

+----------------+------------------------------------------------------------------------------+---------------------------------+---------+
| Parameter      | Description                                                                  | Range                           | Default |
+================+==============================================================================+=================================+=========+
| interface-name | Clears the QoS counters from the specified interface only.                   | ge<interface speed>-<A>/<B>/<C> | \-      |
|                | If you do not specify an [interface-name], all QoS counters will be cleared. |                                 |         |
|                |                                                                              | bundle-<bundle-id>              |         |
|                |                                                                              |                                 |         |
|                |                                                                              | fabm-<f>/<n>/<p>                |         |
|                |                                                                              |                                 |         |
|                |                                                                              | rcym-<f>/<n>/<p>                |         |
|                |                                                                              |                                 |         |
|                |                                                                              | cputx-<f>/<n>/<p>               |         |
|                |                                                                              |                                 |         |
|                |                                                                              | cpurx-<f>/<n>/<p>               |         |
|                |                                                                              |                                 |         |
|                |                                                                              | qppbr-<f>/<n>/<p>               |         |
|                |                                                                              |                                 |         |
+----------------+------------------------------------------------------------------------------+---------------------------------+---------+
| direction      | Clears the QoS counters in the specified direction                           | in                              | \-      |
|                |                                                                              |                                 |         |
|                |                                                                              | out                             |         |
+----------------+------------------------------------------------------------------------------+---------------------------------+---------+


**Example**
::

	dnRouter# clear qos counters
	dnRouter# clear qos counters ge100-1/1/1
	dnRouter# clear qos counters bundle-1
	dnRouter# clear qos counters bundle-1 in


.. **Help line:** clear qos counters attached to interface

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 5.1.0   | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 9.0     | Command not supported                                                             |
+---------+-----------------------------------------------------------------------------------+
| 11.2    | Command re-introduced as part of the new QoS feature                              |
+---------+-----------------------------------------------------------------------------------+
| 15.0    | Added support for fabm and rcym fabric-multicast interface types and cpu counter  |
+---------+-----------------------------------------------------------------------------------+
