network-services nat instance static-snat44-rules internal-ip-list external-ip-list
-----------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the single static source NAT44 N:N rule.

**Command syntax: internal-ip-list [internal-ip-list] external-ip-list [external-ip-list]**

**Command mode:** config

**Hierarchies**

- network-services nat instance static-snat44-rules

**Note**

- The external-ip cannot duplicate with the ip-address within the external-ip-port value of the any static-snapt44-rule.

- The external-ip cannot duplicate with the external-ip value of the any dynamic-snapt44-rule.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| internal-ip-list | List of IP addresses representing the hosts in the internal/private/local        | \-    | \-      |
|                  | network. The list is specified by the allow rules with src-IP in ACL. The other  |       |         |
|                  | (non src-ip) parameters in the ACL rules are disregarded as well as deny rules   |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+
| external-ip-list | List of IP addresses representing the hosts in the internal/private/local        | \-    | \-      |
|                  | network. The list is specified by the allow rules with src-IP in ACL. The other  |       |         |
|                  | (non src-ip) parameters in the ACL rules are disregarded as well as deny rules   |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-snat44-rules
    dnRouter(cfg-inst-stat-snat44)# internal-ip 10.1.1.1/32 external-ip 200.1.1.1/32
    dnRouter(cfg-inst-stat-snat44)# internal-ip 10.2.1.0/24 external-ip 220.1.1.0/24


**Removing Configuration**

To remove specific static source NAT44 1:1 rule
::

    dnRouter(cfg-inst-stat-snat44)# no internal-ip 10.1.1.1/32 external-ip 200.1.1.1/32

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
