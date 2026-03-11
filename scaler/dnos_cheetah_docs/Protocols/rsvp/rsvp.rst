protocols rsvp
--------------

**Minimum user role:** operator

Enters the RSVP configuration hierarchy level.

**Command syntax: rsvp**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)#


**Removing Configuration**

To remove all RSVP configuration:
::

    dnRouter(cfg-protocols)# no rsvp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
