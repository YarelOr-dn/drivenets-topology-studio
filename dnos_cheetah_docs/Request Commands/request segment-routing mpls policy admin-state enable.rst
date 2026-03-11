request segment-routing mpls policy admin-state enable
------------------------------------------------------

**Minimum user role:** operator


To enable the admin-state of SR-TE policy:


**Command syntax: request segment-routing mpls policy [policy-name] admin-state enable**

**Command mode:** operator

**Note:**

- This action does not affect the configuration and it is not persistent.

**Parameter table:**

+-------------+---------------------------------------------------------+
| Parameter   | Description                                             |
+=============+=========================================================+
| policy-name | Enable admin-state for the specified policy.            |
+-------------+---------------------------------------------------------+


**Example:**
::

	dnRouter# request segment-routing mpls policy Auto_c_0_dest_5.5.5.5 admin-state enable


.. **Help line:** Enable the admin-state of SR-TE policy


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 18.2      | Command introduced    |
+-----------+-----------------------+
