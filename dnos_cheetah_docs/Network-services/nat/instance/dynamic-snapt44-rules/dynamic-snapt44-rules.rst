network-services nat instance dynamic-snapt44-rules
---------------------------------------------------

**Minimum user role:** operator

Configure dynamic source NAPT44 N:1 rules.

**Command syntax: dynamic-snapt44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-snapt44-rules
    dnRouter(cfg-inst-dyn-snapt44)#


**Removing Configuration**

To remove all dynamic source NAPT44 N:1 rules
::

    dnRouter(cfg-netsrv-nat-inst)# no dynamic-snapt44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
