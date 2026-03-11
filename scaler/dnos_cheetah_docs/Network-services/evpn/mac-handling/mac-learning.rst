network-services evpn mac-handling mac-learning
-----------------------------------------------

**Minimum user role:** operator

Mac-learning enabled is the default setting for EVPN services.
By defining this knob, mac-learning will be disabled for all new EVPN instances, it will not effect existing services.

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Parameter table**

+--------------+----------------------+--------------+---------+
| Parameter    | Description          | Range        | Default |
+==============+======================+==============+=========+
| mac-learning | Disable MAC Learning | | enabled    | enabled |
|              |                      | | disabled   |         |
+--------------+----------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# mac-learning enabled
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled
::

    no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
