clear rsvp auto-bandwidth
--------------------------

**Minimum user role:** operator

This command resets the auto-bandwidth adjustment interval timer and clears all the collected average-rate samples. The tunnel will continue to use the current bandwidth until the next auto-bandwidth adjustment.

To clear auto-bandwidth information:

**Command syntax: clear rsvp auto-bandwidth** tunnel [tunnel-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**


+-------------+-----------------------------------------------------------------+
| Parameter   | Description                                                     |
+=============+=================================================================+
| tunnel-name | Clear auto-bandwidth information for the specified tunnel only. |
+-------------+-----------------------------------------------------------------+


**Example**
::

	dnRouter# clear rsvp auto-bandwidth

	dnRouter# clear rsvp auto-bandwidth tunnel auto_tunnel_R1_R8_PRIOIRTY_CORE


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+