network-services evpn-vpws-fxc instance protocols bgp
-----------------------------------------------------

**Minimum user role:** operator

To start the BGP process:

**Command syntax: bgp [as-number]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols

**Note**

- The AS-number cannot be changed. To change it, you need to delete the BGP protocol configuration and configure a new process with a different AS-number.

- Notice the change in prompt.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| as-number | The autonomous system number of the router for the evpn-vpws services.  Uses the | 1-4294967295 | \-      |
|           | 32-bit as-number type from the model in RFC 6991.                                |              |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To disable the BGP process:
::

    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# no bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
