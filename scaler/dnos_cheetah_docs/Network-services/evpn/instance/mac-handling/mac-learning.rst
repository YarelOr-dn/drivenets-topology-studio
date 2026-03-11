network-services evpn instance mac-handling mac-learning
--------------------------------------------------------

**Minimum user role:** operator

By default mac-learning is enabled on the local AC interfaces that are associated with this EVPN instance. 
By defining this knob, mac-learning will be disabled on all the AC interfaces of this EVPN instance.

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling

**Parameter table**

+--------------+----------------------+--------------+---------+
| Parameter    | Description          | Range        | Default |
+==============+======================+==============+=========+
| mac-learning | Disable MAC Learning | | enabled    | \-      |
|              |                      | | disabled   |         |
+--------------+----------------------+--------------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dev-dnRouter(cfg-netsrv-evpn)# instance evpn1
    dev-dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dev-dnRouter(cfg-evpn-inst-mh)# mac-learning disabled
    dev-dnRouter(cfg-evpn-inst-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled.
::

    dnRouter(cfg-evpn-inst-mh)# no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
