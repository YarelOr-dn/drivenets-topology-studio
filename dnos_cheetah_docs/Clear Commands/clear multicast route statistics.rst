clear multicast route statistics
--------------------------------

**Minimum user role:** operator

You can use this command to clear the statistics of (S,G) MFIB entries in the multicast route (by source address or group address).

**Command syntax: clear multicast route statistics** group [group-address] source [source-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - Using group [group-address] option clears the statistics of (S,G) multicast route entries with the related G = group address.

 - Using source [source-address] option clears the statistics of (S,G) multicast route entries with the related S = source address.

 - Using group [group-address] source [source-address] options clears the statistics of multicast route entries with S = source-address and G = group-address.


**Parameter table:**

+-------------------+------------------------------------+-----------+-------------+
|                   |                                    |           |             |
| Parameter         | Description                        | Range     | Default     |
+===================+====================================+===========+=============+
|                   |                                    |           |             |
| group-address     | The multicast group IP address     | IPv4      | \-          |
+-------------------+------------------------------------+-----------+-------------+
|                   |                                    |           |             |
| source-address    | The multicast source IP address    | IPv4      | \-          |
+-------------------+------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# clear multicast route statistics
	dnRouter# clear multicast route statistics group 227.2.3.4
	dnRouter# clear multicast route statistics source 12.2.43.12
	dnRouter# clear multicast route statistics group 227.2.3.4 source 12.2.43.12


.. **Help line:** Clear multicast route statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+