network-services multihoming interface designated-forwarder no-preemption
-------------------------------------------------------------------------

**Minimum user role:** operator

Set whether no-premption shall be enabled or disabled.

**Command syntax: no-preemption [no-preemption]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface designated-forwarder

**Parameter table**

+---------------+------------------------------------------------------------------+--------------+---------+
| Parameter     | Description                                                      | Range        | Default |
+===============+==================================================================+==============+=========+
| no-preemption | Whether this PE, when it is the DF, requests not to be preempted | | enabled    | \-      |
|               |                                                                  | | disabled   |         |
+---------------+------------------------------------------------------------------+--------------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# no-preemption enabled
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled.
::

    dnRouter(cfg-mh-int-df)# no no-preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
