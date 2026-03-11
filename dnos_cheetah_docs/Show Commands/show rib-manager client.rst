show rib-manager client
-----------------------

**Minimum user role:** viewer

To display the RIB-manager's running clients:



**Command syntax: show rib-manager client**

**Command mode:** operational



.. **Note**

	- if greceful restart restarter is disabled for a certain protocol than nsf is disabled and no stale time displayed.


**Example**
::

	dnRouter# show rib-manager client
	Client fd 26 (ospfv3, nsf enabled, stale time is 180)
	Client fd 26 (ospf, nsf enabled, stale time is 180)
	Client fd 27 (ldp, nsf enabled, stale time is 240)
	Client fd 29 (bfd)
	Client fd 28 (bgp, nsf enabled, stale time is 180)

	dnRouter# show rib-manager client
	Client fd 26 (ospfv3, nsf disabled)
	Client fd 26 (ospf, nsf enabled, stale time is 180)
	Client fd 27 (ldp, nsf enabled, stale time is 240)
	Client fd 29 (bfd)
	Client fd 28 (bgp, nsf enabled, stale time is 180)

.. **Help line:** show RIB-Manager running clients

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

