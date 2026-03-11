system cprl rsvp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the RSVP protocol:

**Command syntax: rsvp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# rsvp
    dnRouter(cfg-system-cprl-rsvp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the RSVP protocol:
::

    dnRouter(cfg-system-cprl)# no rsvp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
