protocols rsvp bfd
------------------

**Minimum user role:** operator

To enter BFD for RSVP configuration mode:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# bfd
    dnRouter(cfg-protocols-rsvp-bfd)


**Removing Configuration**

To revert all parameters to their default value:
::

    dnRouter(cfg-protocols-rsvp)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
