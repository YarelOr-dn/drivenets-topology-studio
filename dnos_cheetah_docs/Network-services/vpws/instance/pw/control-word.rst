network-services vpws instance pw control-word
----------------------------------------------

**Minimum user role:** operator

The Control-word is always zero when enabled and is used as a marker to identify between the inner layer 2 packet and the layer 3 encapsulation. The Control-word is only used when it is supported by both sides.

**Command syntax: control-word [control-word]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+--------------+-------------------------------+--------------+---------+
| Parameter    | Description                   | Range        | Default |
+==============+===============================+==============+=========+
| control-word | Set control-word usage for PW | | enabled    | enabled |
|              |                               | | disabled   |         |
+--------------+-------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# control-word disabled


**Removing Configuration**

To revert control-word to default:
::

    dnRouter(cfg-vpws-inst-pw)# no control-word

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
