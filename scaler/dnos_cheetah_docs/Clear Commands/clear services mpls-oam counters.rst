clear services mpls-oam counters
--------------------------------

**Minimum user role:** operator

To clear MPLS-OAM service counters:

**Command syntax: clear services mpls-oam counters** {profile [profile-name] \| tunnel-name [tunnel-name] \| auto-mesh [template-name] \| auto-bypass}

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+---------------+------------------------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                                    | Range | Default |
+===============+================================================================================================+=======+=========+
| profile-name  | Clears the counters for MPLS-OAM profile only                                                  | \-    | \-      |
+---------------+------------------------------------------------------------------------------------------------+-------+---------+
| tunnel-name   | Clears the counters for the specified tunnel only                                              | \-    | \-      |
+---------------+------------------------------------------------------------------------------------------------+-------+---------+
| template-name | Clears the counters for the tunnels that were created by the specified auto-mesh template only | \-    | \-      |
+---------------+------------------------------------------------------------------------------------------------+-------+---------+
| auto-bypass   | Clears the counters for auto-bypass tunnels                                                    | \-    | \-      |
+---------------+------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# clear services mpls-oam counters
	dnRouter# clear services mpls-oam counters profile COS_1
	dnRouter# clear services mpls-oam counters tunnel-name tunnel_1


.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+