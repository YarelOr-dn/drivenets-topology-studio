network-services multihoming designated-forwarder no-preemption
---------------------------------------------------------------

**Minimum user role:** operator

Set the default value for whether no-premption is enabled or disabled.
This value can be modified per interface by setting the per-interface knob.

**Command syntax: no-preemption [no-preemption]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+---------------+------------------------------------------------------------------+--------------+----------+
| Parameter     | Description                                                      | Range        | Default  |
+===============+==================================================================+==============+==========+
| no-preemption | Whether this PE, when it is the DF, requests not to be preempted | | enabled    | disabled |
|               |                                                                  | | disabled   |          |
+---------------+------------------------------------------------------------------+--------------+----------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# no-preemption enabled
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To revert the default no-preemption configuration to disabled.
::

    dnRouter(cfg-netsrv-mh-df)# no no-preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
