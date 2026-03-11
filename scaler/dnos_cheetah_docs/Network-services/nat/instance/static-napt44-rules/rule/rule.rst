network-services nat instance static-napt44-rules internal-ip-port external-ip-port protocol
--------------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure a single static NAPT44 1:1 rule.

**Command syntax: internal-ip-port [internal-ip-port] external-ip-port [external-ip-port] protocol [protocol]**

**Command mode:** config

**Hierarchies**

- network-services nat instance static-napt44-rules

**Parameter table**

+------------------+----------------------------------------------+-----------+---------+
| Parameter        | Description                                  | Range     | Default |
+==================+==============================================+===========+=========+
| internal-ip-port | Reference to the configured internal-ip-port | \-        | \-      |
+------------------+----------------------------------------------+-----------+---------+
| external-ip-port | Reference to the configured external-ip-port | \-        | \-      |
+------------------+----------------------------------------------+-----------+---------+
| protocol         | Reference to the configured protocol         | nat-tcp   | \-      |
|                  |                                              | nat-udp   |         |
+------------------+----------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# static-napt44-rules
    dnRouter(cfg-inst-stat-napt44)# internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp
    dnRouter(cfg-inst-stat-napt44)# internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp


**Removing Configuration**

To remove specific static NAPT44 1:1 rule
::

    dnRouter(cfg-inst-stat-napt44)# no internal-ip-port 10.1.1.1:80 external-ip-port 200.1.1.1:8080 protocol tcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
