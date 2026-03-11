network-services nat instance static-napt44-rules
-------------------------------------------------

**Minimum user role:** operator

Configure the static NAPT44 1:1 rules.

**Command syntax: static-napt44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-napt44-rules
    dnRouter(cfg-inst-stat-napt44)#


**Removing Configuration**

To remove all static NAPT44 1:1 rules
::

    dnRouter(cfg-netsrv-nat-inst)# no static-napt44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
