network-services nat instance max-sessions
------------------------------------------

**Minimum user role:** operator

To configure an intenal network facing interface per NAT instance:

**Command syntax: max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter    | Description                                                                      | Range      | Default |
+==============+==================================================================================+============+=========+
| max-sessions | Maximum number of learned dynamic sessions per NAT instance. This number         | 0-10000000 | 1000000 |
|              | includes dyanmic N:M NAT sessions, dyanamic N:1 NAPT sessions, static 1:1 NAPT   |            |         |
|              | rules, static 1:1 NAT rules, dynamic ICMP sessions and dynamic IP-fragmented     |            |         |
|              | sessions. The resource allocation per each session type is according to FCFS     |            |         |
|              | basis  0 - unlimited NAT session tables per instance                             |            |         |
+--------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# max-sessions 1000000
    dnRouter(cfg-netsrv-nat-inst)#


**Removing Configuration**

To set maximum number of sessions per NAT instance to default:
::

    dnRouter(cfg-netsrv-nat)# no max-sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
