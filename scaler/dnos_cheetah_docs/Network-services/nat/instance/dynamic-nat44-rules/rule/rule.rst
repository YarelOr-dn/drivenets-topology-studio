network-services nat instance dynamic-nat44-rules internal-ip-list external-ip-pool
-----------------------------------------------------------------------------------

**Minimum user role:** operator

Configure a single dynamic NAPT44 N:1 rule.

**Command syntax: internal-ip-list [internal-ip-list] external-ip-pool [external-ip-pool]**

**Command mode:** config

**Hierarchies**

- network-services nat instance dynamic-nat44-rules

**Parameter table**

+------------------+----------------------------------------------+---------------+---------+
| Parameter        | Description                                  | Range         | Default |
+==================+==============================================+===============+=========+
| internal-ip-list | Reference to the configured internal-ip-list | \-            | \-      |
+------------------+----------------------------------------------+---------------+---------+
| external-ip-pool | Reference to the configured external-ip-pool | string        | \-      |
|                  |                                              | length 1..32  |         |
+------------------+----------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-nat44-rules
    dnRouter(cfg-inst-dyn-nat44)# internal-ip-list MyAccessList external-ip-pool MyAddressPool
    dnRouter(cfg-inst-dyn-nat44)# internal-ip-list MyAccessList2 external-ip-pool MyAddressPool2


**Removing Configuration**

To remove specific dynamic NAT44 N:M rule
::

    dnRouter(cfg-inst-dyn-nat44)# no internal-ip-list MyAccessList2 external-ip-pool MyAddressPool

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
