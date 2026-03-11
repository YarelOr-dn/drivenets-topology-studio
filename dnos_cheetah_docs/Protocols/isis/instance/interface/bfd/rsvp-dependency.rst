protocols isis instance interface bfd rsvp-dependency
-----------------------------------------------------

**Minimum user role:** operator

Configure BFD IPv4 for IS-IS to trigger RSVP -TE FRR events. When set, a failure on an IPv4 SH-BFD session protecting IS-IS adjacency will also trigger local an FRR reaction in FIB & RSVP.

**Command syntax: rsvp-dependency [rsvp-dependency]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Parameter table**

+-----------------+----------------------------------------------------+--------------+----------+
| Parameter       | Description                                        | Range        | Default  |
+=================+====================================================+==============+==========+
| rsvp-dependency | The administrative state of the BFD IPv4 for IS-IS | | enabled    | disabled |
|                 |                                                    | | disabled   |          |
+-----------------+----------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# rsvp-dependency enabled


**Removing Configuration**

To revert all BFD configuration to their default values
::

    dnRouter(cfg-inst-if-bfd)# no rsvp-dependency

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
