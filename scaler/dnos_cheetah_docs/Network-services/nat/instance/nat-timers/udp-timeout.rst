network-services nat instance nat-timers udp-timeout
----------------------------------------------------

**Minimum user role:** operator

Configure the NAT timeout value for the UDP sessions.

**Command syntax: udp-timeout [udp-timeout]**

**Command mode:** config

**Hierarchies**

- network-services nat instance nat-timers

**Parameter table**

+-------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter   | Description                                                                      | Range   | Default |
+=============+==================================================================================+=========+=========+
| udp-timeout | Amount of time for idle UDP session to be retired from the NAT session table.    | 10-7440 | 300     |
|             | The default value is taken from RFC4787 Section 4.3                              |         |         |
+-------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)# udp-timeout 120
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set UDP timeout timer to default
::

    dnRouter(cfg-nat-inst-timers)# no udp-timeout"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
