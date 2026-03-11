network-services nat instance dynamic-snat44-rules internal-ip-list external-ip-pool
------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure single dynamic source NAPT44 N:1 rule

**Command syntax: internal-ip-list [internal-ip-list] external-ip-pool [external-ip-pool]**

**Command mode:** config

**Hierarchies**

- network-services nat instance dynamic-snat44-rules

**Note**

- any ip-address within external-ip-pool cannot duplicate with ip-address within external-ip-port value of any static-snapt44-rule

- any ip-address within external-ip-pool cannot duplicate with external-ip value of any dynamic-snapt44-rule

**Parameter table**

+------------------+----------------------------------------------+-------+---------+
| Parameter        | Description                                  | Range | Default |
+==================+==============================================+=======+=========+
| internal-ip-list | Reference to the configured internal-ip-list | \-    | \-      |
+------------------+----------------------------------------------+-------+---------+
| external-ip-pool | Reference to the configured external-ip-pool | \-    | \-      |
+------------------+----------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-snat44-rules
    dnRouter(cfg-inst-dyn-snat44)# internal-ip-list MyAccessList external-ip-pool MyAddressPool
    dnRouter(cfg-inst-dyn-snat44)# internal-ip-list MyAccessList2 external-ip-pool MyAddressPool2


**Removing Configuration**

To remove specific dynamic source NAT44 N:M rule
::

    dnRouter(cfg-inst-dyn-snat44)# no internal-ip-list MyAccessList2 external-ip-pool MyAddressPool

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
