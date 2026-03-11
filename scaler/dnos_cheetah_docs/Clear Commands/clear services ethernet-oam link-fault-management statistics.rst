clear services ethernet-oam link-fault-management statistics
------------------------------------------------------------

**Minimum user role:** operator

To clear ethernet OAM link-fault-management service counters:

**Command syntax: clear services ethernet-oam link-fault-management statistics** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+----------------+------------------------------------------------------------------+---------------------------------+---------+
| Parameter      | Description                                                      | Range                           | Default |
+================+==================================================================+=================================+=========+
| interface-name | Clears ethernet OAM LFM statistics for a specific interface      | ge<interface speed>-<A>/<B>/<C> | \-      |
+----------------+------------------------------------------------------------------+---------------------------------+---------+

**Example**
::

	dnRouter# clear services ethernet-oam link-fault-management statistics
	dnRouter# clear services ethernet-oam link-fault-management statistics ge100-0/0/19


.. **Help line:** clear 802.3ah EFM link-OAM statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
