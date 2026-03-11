network-services nat instance static-snapt44-rules internal-ip-port external-ip-port protocol
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the single static source NAPT44 1:1 rule.

**Command syntax: internal-ip-port [internal-ip-port] external-ip-port [external-ip-port] protocol [protocol]**

**Command mode:** config

**Hierarchies**

- network-services nat instance static-snapt44-rules

**Note**

- The ip-address within the external-ip-port cannot duplicate with the external-ip value of the any static-snat44-rule.

- The ip-address within the external-ip-port cannot duplicate with the any address in the external-ip-pool of the any dynamic-snat44-rule.

**Parameter table**

+------------------+----------------------------------------------+---------+---------+
| Parameter        | Description                                  | Range   | Default |
+==================+==============================================+=========+=========+
| internal-ip-port | Reference to the configured internal-ip-port | \-      | \-      |
+------------------+----------------------------------------------+---------+---------+
| external-ip-port | Reference to the configured external-ip-port | \-      | \-      |
+------------------+----------------------------------------------+---------+---------+
| protocol         | Reference to the configured protocol         | | tcp   | \-      |
|                  |                                              | | udp   |         |
+------------------+----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-snapt44-rules
    dnRouter(cfg-inst-stat-snapt44)# internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp
    dnRouter(cfg-inst-stat-snapt44)# internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp


**Removing Configuration**

To remove specific static source NAPT44 1:1 rule
::

    dnRouter(cfg-inst-stat-snapt44)# no internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
