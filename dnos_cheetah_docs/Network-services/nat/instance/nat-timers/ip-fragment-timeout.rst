network-services nat instance nat-timers ip-fragmented-timeout
--------------------------------------------------------------

**Minimum user role:** operator

Configure the NAT timeout value for IP-Fragmented sessions.

**Command syntax: ip-fragmented-timeout [ip-fragmented-timeout]**

**Command mode:** config

**Hierarchies**

- network-services nat instance nat-timers

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter             | Description                                                                      | Range  | Default |
+=======================+==================================================================================+========+=========+
| ip-fragmented-timeout | Amount of time for idle IP fragmentation session to be retired from the NAT      | 10-120 | 10      |
|                       | fragmented session table. The default value is taken from RFC4963 Section 2      |        |         |
+-----------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)# ip-fragmented-timeout 120
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set IP-Fragmented timeout timer to default
::

    dnRouter(cfg-nat-inst-timers)# no ip-fragmeneted-timeout"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
