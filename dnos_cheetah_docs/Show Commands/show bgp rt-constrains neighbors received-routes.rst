show bgp rt-constrains neighbors received-routes
------------------------------------------------

**Minimum user role:** viewer

To display received routes under rt-constrains neighbors sessions:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] rt-constrains neighbors [neighbor-address] received-routes** nlri [nlri]

**Command mode:** operational

**Note**

-  Use "nlri" to display detailed information matching a specific NLRI.

.. -  nlri - require to use apostrophes when entring the nlri string


**Parameter table**

+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+
|     Parameter    | Description                                                                                   |       Range       | Default |
+==================+===============================================================================================+===================+=========+
| vrf-name         | Displays routing information for a non-default VRF                                            | 1..255 characters | \-      |
+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+
| address-family   | Display routing information for a specific address-family (AFI)                               | IPv4              | \-      |
+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+
| neighbor-address | The neighbor address                                                                          | A.B.C.D           | \-      |
|                  |                                                                                               | xx:xx::xx:xx      |         |
+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+
| received-routes  | Displays the routes received from a BGP neighbor                                              | \-                | \-      |
+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+
| nlri             | Filter the displayed information for a specific Network Layer Reachability Information (nlri) | \-                | \-      |
+------------------+-----------------------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# show bgp ipv4 rt-constrains neighbors 1.1.1.1 received-routes 4200000000:16:1000


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
