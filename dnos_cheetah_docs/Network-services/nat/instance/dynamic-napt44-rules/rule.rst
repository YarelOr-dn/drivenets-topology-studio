network-services nat instance dynamic-napt44-rules internal-ip-list external-ip
-------------------------------------------------------------------------------

**Minimum user role:** operator

Configure a single dynamic NAPT44 N:1 rule.

**Command syntax: internal-ip-list [internal-ip-list] external-ip [external-ip]**

**Command mode:** config

**Hierarchies**

- network-services nat instance dynamic-napt44-rules

**Note**

- The ip-address within the external-ip-port cannot duplicate with the external-ip value of any static-nat44-rule.

- The ip-address within the external-ip-port cannot duplicate with the ip-address within the external-ip-port value of any static-napt44-rule.

- The ip-address within the external-ip-port cannot duplicate with any address in the the external-ip-pool of the any dynamic-nat44-rule.

**Parameter table**

+------------------+----------------------------------------------+---------+---------+
| Parameter        | Description                                  | Range   | Default |
+==================+==============================================+=========+=========+
| internal-ip-list | Reference to the configured internal-ip-list | \-      | \-      |
+------------------+----------------------------------------------+---------+---------+
| external-ip      | Reference to the configured external-ip      | A.B.C.D | \-      |
+------------------+----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# dynamic-napt44-rules
    dnRouter(cfg-inst-dyn-napt44)# internal-ip-list MyAccessList external-ip 200.1.1.1
    dnRouter(cfg-inst-dyn-napt44)# internal-ip-list MyAccessList2 external-ip 200.1.1.1


**Removing Configuration**

To remove specific dynamic NAPT44 N:1 rule
::

    dnRouter(cfg-inst-dyn-napt44)# no internal-ip-list MyAccessList2 external-ip 200.1.1.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
