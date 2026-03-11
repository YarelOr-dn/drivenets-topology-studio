show bgp flowspec neighbors
---------------------------

**Minimum user role:** viewer

To display detailed information on TCP and BGP neighbor connections:


**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] flowspec neighbors** [neighbor-address]

**Command mode:** operational



**Note**
 
- Set neighbor-address to display information for a specific neighbor, otherwise information will be displayed for all flowspec neighbor sessions.

**Parameter table**

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter         | Description                                                                                                                                             | Range                       |
+===================+=========================================================================================================================================================+=============================+
| vrf-name          | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family    | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                   |                                                                                                                                                         | IPv6                        |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| neighbor-address  | Neighbor address                                                                                                                                        | A.B.C.D                     |
|                   |                                                                                                                                                         | xx:xx::xx:xx                |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 flowspec neighbors

	dnRouter# show bgp ipv4 flowspec neighbors 1.1.1.1


.. **Help line:**

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 13.0    | Command introduced                 |
+---------+------------------------------------+

