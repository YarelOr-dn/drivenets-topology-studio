clear ber counters
------------------

**Minimum user role:** operator

To clear the bit error rate counters:

**Command syntax: clear ber counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**
 - clear ber counters** clears all BER counters

**Parameter table:**

+-------------------+---------------------------------------------------------------+--------------------------------+-------------+
| Parameter         | Description                                                   | Range                          | Default     |
+===================+===============================================================+================================+=============+
| interface-name    | Clears the BER counters from the specified interface only.    | ge<interface speed>-<A>/<B>/<C>| \-          |
+-------------------+---------------------------------------------------------------+--------------------------------+-------------+


**Example**
::

	dnRouter# clear ber counters
	dnRouter# clear ber counters ge400-2/0/3


.. **Help line:** Clear 400GE and 100GE physical interfaces with FEC BER signaling statistics

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 17.2        | Command introduced    |
+-------------+-----------------------+
