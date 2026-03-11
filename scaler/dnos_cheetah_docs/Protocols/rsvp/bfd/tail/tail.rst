protocols rsvp bfd tail
-----------------------

**Minimum user role:** operator

To enter BFD-Tail for RSVP configuration mode:

**Command syntax: tail**

**Command mode:** config

**Hierarchies**

- protocols rsvp bfd

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# bfd
    dnRouter(cfg-protocols-rsvp-bfd)# tail


**Removing Configuration**

To revert all tail configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp-bfd)# no tail

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
