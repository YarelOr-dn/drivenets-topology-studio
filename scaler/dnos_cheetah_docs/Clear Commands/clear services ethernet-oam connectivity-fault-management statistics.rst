clear services ethernet-oam connectivity-fault-management statistics
--------------------------------------------------------------------

**Minimum user role:** operator

To clear the ethernet OAM 802.1ag connectivity-fault-management service counters:

**Command syntax: clear services ethernet-oam connectivity-fault-management statistics {[interface-name] | maintenance-domain [md-name] | maintenance-domain [md-name] maintenance-association [ma-name] | maintenance-domain [md-name] maintenance-association [ma-name] mep-id [local-mep-id] | all}**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+----------------+--------------------------------------------------------------------+------------------------------------------+---------+
| Parameter      | Description                                                        | Range                                    | Default |
+================+====================================================================+==========================================+=========+
| interface-name | Clears ethernet OAM CFM statistics for a specific interface        | geX-<f>/<n>/<p>                          | \-      |
|                |                                                                    | geX-<f>/<n>/<p>[.<sub-interface id>]     |         |
|                |                                                                    | bundle-<bundle id>                       |         |
|                |                                                                    | bundle-<bundle id>[.<sub-interface id>]  |         |
+----------------+--------------------------------------------------------------------+------------------------------------------+---------+
| md-name        | The name of the Maintenance Domain                                 | String                                   | \-      |
+----------------+--------------------------------------------------------------------+------------------------------------------+---------+
| ma-name        | The name of the Maintenance Association under a Maintenance Domain | String                                   | \-      |
+----------------+--------------------------------------------------------------------+------------------------------------------+---------+
| local-mep-id   | The identifier of the local MEP in the Maintenance Association     | 1-8191                                   | \-      |
+----------------+--------------------------------------------------------------------+------------------------------------------+---------+
| all            | Clears all ethernet OAM CFM statistics in the system               | \-                                       | \-      |
+----------------+--------------------------------------------------------------------+------------------------------------------+---------+

**Example**
::

	dnRouter# clear services ethernet-oam connectivity-fault-management statistics ge100-0/0/19
	dnRouter# clear services ethernet-oam connectivity-fault-management statistics maintenance-domain MD1
	dnRouter# clear services ethernet-oam connectivity-fault-management statistics maintenance-domain MD1 maintenance-association MA1
	dnRouter# clear services ethernet-oam connectivity-fault-management statistics maintenance-domain MD1 maintenance-association MA1 mep-id 3
	dnRouter# clear services ethernet-oam connectivity-fault-management statistics all


.. **Help line:** clear 802.1ag CFM statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+