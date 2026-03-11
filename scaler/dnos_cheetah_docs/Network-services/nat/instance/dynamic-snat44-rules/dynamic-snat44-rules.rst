network-services nat instance dynamic-snat44-rules
--------------------------------------------------

**Minimum user role:** operator

Configure dynamic source NAT44 N:M rules.

**Command syntax: dynamic-snat44-rules**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-snat44-rules
    dnRouter(cfg-inst-dyn-snat44)#


**Removing Configuration**

To remove all dynamic source NAT44 N:M rules
::

    dnRouter(cfg-netsrv-nat-inst)# no dynamic-snat44-rules

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
