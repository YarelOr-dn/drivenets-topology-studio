network-services bridge-domain instance mac-handling mac-learning
-----------------------------------------------------------------

**Minimum user role:** operator

The default mac-learning setting is defined by the global Bridge Domain settings. 
This knob, allows the mac-learning to be enabled/disabled on all the AC interfaces of this Bridge-Domain instance.

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance mac-handling

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
    dev-dnRouter(cfg-netsrv-bd)# instance bd1
    dev-dnRouter(cfg-netsrv-bd-inst)# mac-handling
    dev-dnRouter(cfg-bd-inst-mh)# mac-learning disabled
    dev-dnRouter(cfg-bd-inst-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled.
::

    dnRouter(cfg-bd-inst-mh)# no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
