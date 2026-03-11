clear rsvp statistics tunnels
-----------------------------

**Minimum user role:** operator

To clear statistics for RSVP tunnels:

**Command syntax: clear rsvp statistics tunnels** name [tunnel-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**


**Parameter table:**

+-------------+------------------------------------------------------------+
| Parameter   | Description                                                |
+=============+============================================================+
| tunnel-name | Clear RSVP statistics from the specified RSVP tunnel only. |
+-------------+------------------------------------------------------------+


**Example**
::

	dnRouter# clear rsvp statistics tunnels
	dnRouter# clear rsvp statistics tunnels name TUNNEL_1

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+