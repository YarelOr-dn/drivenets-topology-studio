network-services nat instance static-snat44-rules
-------------------------------------------------

**Minimum user role:** operator

Configure the static source NAT44 1:1 rules.

**Command syntax: static-snat44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-snat44-rules
    dnRouter(cfg-inst-stat-snat44)#


**Removing Configuration**

To remove all static source NAT44 1:1 rules
::

    dnRouter(cfg-netsrv-nat-inst)# no static-snat44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
