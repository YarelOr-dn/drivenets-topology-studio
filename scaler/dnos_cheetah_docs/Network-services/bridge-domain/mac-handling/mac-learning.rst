network-services bridge-domain mac-handling mac-learning
--------------------------------------------------------

**Minimum user role:** operator

This default mac-learning setting defines the default value that will be set for any new bridge-domain instances. 

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+--------------+----------------------+--------------+---------+
| Parameter    | Description          | Range        | Default |
+==============+======================+==============+=========+
| mac-learning | Disable MAC Learning | | enabled    | enabled |
|              |                      | | disabled   |         |
+--------------+----------------------+--------------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dev-dnRouter(cfg-netsrv-bd)# mac-handling
    dev-dnRouter(cfg-netsrv-bd-mh)# mac-learning disabled
    dev-dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
