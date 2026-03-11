network-services nat instance internal-if
-----------------------------------------

**Minimum user role:** operator

To configure an intenal network facing interface per NAT instance:

**Command syntax: internal-if [internal-if]**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Note**

- Only NAT virtual interfaces are allowed to be used.

- NAT virtal interface must be associated with port-pairs that include only SGEs with nat-mode: internal.

**Parameter table**

+-------------+------------------------------------+------------------+---------+
| Parameter   | Description                        | Range            | Default |
+=============+====================================+==================+=========+
| internal-if | Internal network facing interface  | | string         | \-      |
|             |                                    | | length 1-255   |         |
+-------------+------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# internal-if nat-1
    dnRouter(cfg-netsrv-nat-inst)#


**Removing Configuration**

To remove the internal-if from specified NAT instance:
::

    dnRouter(cfg-netsrv-nat)# no internal-if

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
