network-services nat instance static-snapt44-rules
--------------------------------------------------

**Minimum user role:** operator

Configure the static source NAPT44 1:1 rules.

**Command syntax: static-snapt44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-snapt44-rules
    dnRouter(cfg-inst-stat-snapt44)#


**Removing Configuration**

To remove all static source NAPT44 1:1 rules
::

    dnRouter(cfg-netsrv-nat-inst)# no static-snapt44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
