network-services nat instance nat-timers
----------------------------------------

**Minimum user role:** operator

Configure the NAT timeout values.

**Command syntax: nat-timers**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set all the NAT timeout values to default
::

    dnRouter(cfg-netsrv-nat-inst)# no nat-timers"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
