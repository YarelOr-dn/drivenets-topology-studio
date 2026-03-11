network-services nat instance static-dnat44-rules internal-ip external-ip
-------------------------------------------------------------------------

**Minimum user role:** operator

Configure the single static destination NAT44 1:1 rule.

**Command syntax: internal-ip [internal-ip] external-ip [external-ip]**

**Command mode:** config

**Hierarchies**

- network-services nat instance static-dnat44-rules

**Note**

- The external-ip cannot duplicate with the ip-address within the external-ip-port value of the any static-dnapt44-rule.

**Parameter table**

+-------------+-----------------------------------------+---------+---------+
| Parameter   | Description                             | Range   | Default |
+=============+=========================================+=========+=========+
| internal-ip | Reference to the configured internal-ip | A.B.C.D | \-      |
+-------------+-----------------------------------------+---------+---------+
| external-ip | Reference to the configured external-ip | A.B.C.D | \-      |
+-------------+-----------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-dnat44-rules
    dnRouter(cfg-inst-stat-dnat44)# internal-ip 10.1.1.1 external-ip 200.1.1.1
    dnRouter(cfg-inst-stat-dnat44)# internal-ip 10.2.1.1 external-ip 220.1.1.1


**Removing Configuration**

To remove specific static destination NAT44 1:1 rule
::

    dnRouter(cfg-inst-stat-dnat44)# no internal-ip 10.1.1.1 external-ip 200.1.1.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
