show ospfv3 route
-----------------

**Minimum user role:** viewer

To displays OSPF routes, as determined by the most recent SPF calculation.



**Command syntax: show ospfv3 route**

**Command mode:** operational


**Example**
::

  dnRouter# show ospfv3 route

  * 177:0:1::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1001
  * 177:0:2::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1002
  * 177:0:3::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1003
  * 177:0:4::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1004
  * 177:0:5::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1005
  * 177:0:6::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1006
  * 177:0:7::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1007
  * 177:0:8::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1008
  * 177:0:9::/64, Intra-Area, cost [1/0], area 0.0.0.0
      :: ge100-0/0/3.1009
  * 177:0:a::/64, Intra-Area, cost [1/0], area 0.0.0.0
  * 2611::/64, Intra-Area, cost [40/0], area 0.0.0.0
      :: ge100-0/0/0.2501
    2611::/64, Intra-Area, cost [41/0], area 0.0.0.0
      fe80::2bc:60ff:fe48:78bc ge100-0/0/0.2500
      fe80::2bc:60ff:fe48:78bc ge100-0/0/0.2501
  * 9999::1/128, Intra-Area, cost [40/0], area 0.0.0.0
      fe80::2bc:60ff:fe48:78bc ge100-0/0/0.2500
      fe80::2bc:60ff:fe48:78bc ge100-0/0/0.2501

.. **Help line:** Displays the OSPFv3 route information.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+


