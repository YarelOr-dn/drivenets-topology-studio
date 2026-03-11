network-services nat instance nat-timers ip-timeout
---------------------------------------------------

**Minimum user role:** operator

Configure the NAT timeout value for any IP translation done according to NAT N:M dynamic translations.

**Command syntax: ip-timeout [ip-timeout]**

**Command mode:** config

**Hierarchies**

- network-services nat instance nat-timers

**Parameter table**

+------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter  | Description                                                                      | Range    | Default |
+============+==================================================================================+==========+=========+
| ip-timeout | Amount of time for idle IP session to be retired from the NAT session table.     | 10-10000 | 7440    |
|            | E.g. GRE or IPSEC session                                                        |          |         |
+------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)# ip-timeout 120
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set IP timeout timer to default
::

    dnRouter(cfg-nat-inst-timers)# no ip-timeout"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
