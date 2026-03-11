show bgp labels vrf all
-----------------------

**Minimum user role:** viewer

To display local VPN labela per vrf information:

**Command syntax: show bgp labels vrf all**

**Command mode:** operational

**Parameter table:**

+---------------------+----------------------------------------------------------------------------+-------+---------+
| Parameter           | Description                                                                | Range | Default |
+=====================+============================================================================+=======+=========+
| vrf-name            | The locally configured vrf name                                            |       | \-      |
+---------------------+----------------------------------------------------------------------------+-------+---------+
| vrf-ID              | The locally assigned ID to the vrf                                         |       | \-      |
+---------------------+----------------------------------------------------------------------------+-------+---------+
| route-distinguisher | The RD configured in the bgp vrf instance                                  |       | \-      |
+---------------------+----------------------------------------------------------------------------+-------+---------+
| VRF Local Label     | The Local label assigned per vrf to classify traffic belonging to that vrf |       | \-      |
+---------------------+----------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# show bgp labels vrf all
	   | VRF-Name                            | VRF-ID       | Route-Distinguisher |  VRF Local Label |
       -----------------------------------------------------------------------------------------------
       | VRF_1                               |            1 |                 1:1 |          1040576 |
       | VRF_2                               |            2 |            202020:2 |          1040577 |
       | VRF_3                               |            3 |           3.3.3.3:3 |          1040578 |



.. **Help line:** Display Local VPN label per vrf information

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
