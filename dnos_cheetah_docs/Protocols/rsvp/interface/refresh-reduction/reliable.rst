protocols rsvp interface refresh-reduction reliable
---------------------------------------------------

**Minimum user role:** operator

Use the reliable attribute to use the message ID and summary refresh for RSVP messages. Doing so reduces the amount of information transmitted every refresh interval.
To enable or disable reliable message delivery for the interface:

**Command syntax: reliable [reliable]**

**Command mode:** config

**Hierarchies**

- protocols rsvp interface refresh-reduction

**Parameter table**

+-----------+-----------------------------------------------+--------------+---------+
| Parameter | Description                                   | Range        | Default |
+===========+===============================================+==============+=========+
| reliable  | Set RSVP message bundling and summary refresh | | enabled    | \-      |
|           |                                               | | disabled   |         |
+-----------+-----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)# refresh-reduction
    dnRouter(cfg-rsvp-if-rr)# reliable disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-rsvp-if-rr)# no reliable

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
