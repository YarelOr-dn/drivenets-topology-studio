network-services bridge-domain mac-handling
-------------------------------------------

**Minimum user role:** operator

Enter the mac-learning hierarchy to modify the mac-learning attributes for this bridge-domain instance.

**Command syntax: mac-handling**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# mac-handling
    dnRouter(cfg-bd-inst-mh)#


**Removing Configuration**

To revert the mac-handling configurations to defaults
::

    dnRouter(cfg-bd-inst)# no mac-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
