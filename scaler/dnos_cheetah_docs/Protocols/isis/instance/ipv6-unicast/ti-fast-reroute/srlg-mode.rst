protocols isis instance address-family ipv6-unicast ti-fast-reroute srlg-mode
-----------------------------------------------------------------------------

**Minimum user role:** operator

Define the SRLG disjointment constraint.
loose (default) - Require srlg disjoint between protected egress interface and protecting path local egress interface , if disjoint alternate path not found, DNOS will provide an LFA path (assuming such exists) without ANY SRLG consideration.
loose-full-path - Require srlg disjoint between protected egress interface and all links of protecting path. if disjoint alternate path not found, DNOS will provide an LFA path (assuming such exists) without ANY SRLG consideration.
strict - Require srlg disjoint between protected egress interface and protecting path local egress interface , if disjoint alternate path not found, no alternate path will be provided.
strict-full-path - Require srlg disjoint between protected egress interface and all links of protecting path. if disjoint alternate path not found, no alternate path will be provided.

To set SRLG-mode:

**Command syntax: srlg-mode [srlg-mode]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast ti-fast-reroute

**Note**

- loose-full-path/strict-full-path mode has compute resource penelty and it will take longer to find ti-fast-reroute alternate paths

- The configuration has no effect if the protection mode is not SRLG disjoint.

**Parameter table**

+-----------+-----------------------------------------+----------------------+---------+
| Parameter | Description                             | Range                | Default |
+===========+=========================================+======================+=========+
| srlg-mode | Define the srlg disjointment constraint | | loose              | loose   |
|           |                                         | | loose-full-path    |         |
|           |                                         | | strict             |         |
|           |                                         | | strict-full-path   |         |
+-----------+-----------------------------------------+----------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-mode strict
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-mode loose-full-path


**Removing Configuration**

To revert the srlg-mode to the default behavior:
::

    dnRouter(cfg-inst-afi-ti-frr)# no srlg-mode

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 18.1    | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 18.3    | Diffrentiate between loose and strict and add full-path constraint |
+---------+--------------------------------------------------------------------+
