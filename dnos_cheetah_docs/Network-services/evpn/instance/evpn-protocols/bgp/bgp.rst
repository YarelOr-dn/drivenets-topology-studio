network-services evpn instance protocols bgp
--------------------------------------------

**Minimum user role:** operator

To start the BGP process:

**Command syntax: bgp [as-number]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance protocols

**Note**

- The AS-number cannot be changed. To change it, you need to delete the BGP protocol configuration and configure a new process with a different AS-number.

- Notice the change in prompt.

**Parameter table**

+-----------+------------------------+--------------+---------+
| Parameter | Description            | Range        | Default |
+===========+========================+==============+=========+
| as-number | peer-group unique name | 1-4294967295 | \-      |
+-----------+------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# protocols
    dnRouter(cfg-evpn-inst-protocols)# bgp-services
    dnRouter(cfg-inst-protocols-bgps)# bgp 65000
    dnRouter(cfg-protocols-bgps-bgp)#


**Removing Configuration**

To disable the BGP process:
::

    dnRouter(cfg-inst-protocols-bgps)# no bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
