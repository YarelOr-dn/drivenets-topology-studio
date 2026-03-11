network-services vpws instance pw mtu
-------------------------------------

**Minimum user role:** operator

Configure the MTU value to be sent (signaled) in a VPWS Pseudowire FEC. By default, the sent MTU value is for each VPWS interface. The MTU sent and received values must match for the Pseudowire to be up if the parameter 'ignore-mtu-mismatch' is disabled.

**Command syntax: mtu [mtu]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+------------------------------------+-----------+---------+
| Parameter | Description                        | Range     | Default |
+===========+====================================+===========+=========+
| mtu       | MTU value to be signaled in PW FEC | 1514-9300 | \-      |
+-----------+------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# mtu 2000


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-vpws-inst-pw)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
