network-services nat instance dynamic-nat44-rules
-------------------------------------------------

**Minimum user role:** operator

Configure dynamic NAT44 N:M rules.

**Command syntax: dynamic-nat44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-nat44-rules
    dnRouter(cfg-inst-dyn-nat44)#


**Removing Configuration**

To remove all dynamic NAT44 N:M rules
::

    dnRouter(cfg-netsrv-nat-inst)# no dynamic-nat44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
