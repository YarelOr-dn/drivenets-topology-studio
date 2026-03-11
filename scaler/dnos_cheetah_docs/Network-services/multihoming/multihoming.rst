network-services multihoming
----------------------------

**Minimum user role:** operator

When an CE device is connected to two different core PE devices for redundancy and loadsharing purposes, this is referred to as a multihomw=ed CE device .
Under the multihoming branch the ACs which are multihomed can be defined.
To enter the multihoming configuration mode:

**Command syntax: multihoming**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# multihoming
    dnRouter(cfg-network-services-mh)#


**Removing Configuration**

To remove all multihoming configurations:
::

    dnRouter(cfg-network-services)# no multihoming

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
