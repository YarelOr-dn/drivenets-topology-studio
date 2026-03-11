clear bgp redistribute
----------------------

**Minimum user role:** operator

To re-evaluate all redistributed routes:

**Command syntax: clear bgp** instance vrf [vrf-name] **redistribute {connected \| ospf \| static}**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table**

+---------------+--------------------------------------------------+-------+-------------+
|               |                                                  | Range |             |
| Parameter     | Description                                      |       | Default     |
+===============+==================================================+=======+=============+
|               |                                                  |       |             |
| vrf-name      | Clear only routes belonging to the specified VRF | \-    | \ -         |
+---------------+--------------------------------------------------+-------+-------------+
|               |                                                  |       |             |
| static        | Clear only static redistributed routes           | \-    | \ -         |
+---------------+--------------------------------------------------+-------+-------------+
|               |                                                  |       |             |
| OSPF          | Clear only OSPF redistributed routes             | \-    | \ -         |
+---------------+--------------------------------------------------+-------+-------------+
|               |                                                  |       |             |
| connected     | Clear only connected redistributed routes        | \-    | \ -         |
+---------------+--------------------------------------------------+-------+-------------+

**Example**
::

	dnRouter# clear bgp redistribute static
	dnRouter# clear bgp redistribute ospf
	dnRouter# clear bgp redistribute connected

	dnRouter# clear bgp instance vrf A redistribute static
	dnRouter# clear bgp instance vrf A redistribute ospf
	dnRouter# clear bgp instance vrf A redistribute connected


.. **Help line:**

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+