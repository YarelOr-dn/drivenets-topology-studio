network-services nat instance external-if
-----------------------------------------

**Minimum user role:** operator

To configure an intenal network facing interface per NAT instance:

**Command syntax: external-if [external-if]**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Note**

- Only NAT virtual exterfaces are allowed to be used.

- NAT virtal interface must be associated with port-pairs that include only SGEs with nat-mode: external.

**Parameter table**

+-------------+------------------------------------+------------------+---------+
| Parameter   | Description                        | Range            | Default |
+=============+====================================+==================+=========+
| external-if | External network facing interface  | | string         | \-      |
|             |                                    | | length 1-255   |         |
+-------------+------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# external-if nat-1
    dnRouter(cfg-netsrv-nat-inst)#


**Removing Configuration**

To remove the external-if from specified NAT instance:
::

    dnRouter(cfg-netsrv-nat)# no external-if

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
