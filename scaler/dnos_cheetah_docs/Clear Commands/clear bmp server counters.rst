clear bmp server counters
-------------------------

**Minimum user role:** operator

To reset the bmp session messages counters:

**Command syntax: clear bmp server** [server-id] **counters** neighbor [neighbor-address]

**Command mode:** operation

.. **Hierarchies**

**Note**

- A command without a specific session-id clears counters per all configured bmp servers.

.. - neighbor-address - clear for counters of messages related to a specific neighbor

.. - support auto-complete for configured server-id

**Parameter table:**

+---------------------+--------------------------+-----------------------+-------------+
|                     |                          |                       |             |
| Parameter Name      | Description              | Range                 | Default     |
+=====================+==========================+=======================+=============+
|                     | The id of the bmp server | 0..4                  | \-          |
| server-id           |                          |                       |             |
+---------------------+--------------------------+-----------------------+-------------+
|                     | The neighbor ip address  | A.B.C.D               | \-          |
| neighbor-address    |                          | {ipv6 address format} |             |
+---------------------+--------------------------+-----------------------+-------------+


**Example**
::

	dnRouter# clear bmp server counters
	dnRouter# clear bmp server 0 counters
	dnRouter# clear bmp server counters neighbor 2.2.2.2
	dnRouter# clear bmp server 1 counters neighbor 2.2.2.2


.. **Help line:** Clear bmp session messages counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.1        | Command introduced    |
+-------------+-----------------------+