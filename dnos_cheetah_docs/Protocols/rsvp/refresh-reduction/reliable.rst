protocols rsvp refresh-reduction reliable
-----------------------------------------

**Minimum user role:** operator

Use the reliable attribute to use the message ID and summary refresh for RSVP messages. Doing so reduces the amount of information transmitted every refresh interval.
To enable or disable reliable message delivery:

**Command syntax: reliable [reliable]**

**Command mode:** config

**Hierarchies**

- protocols rsvp refresh-reduction

**Parameter table**

+-----------+-----------------------------------------------+--------------+---------+
| Parameter | Description                                   | Range        | Default |
+===========+===============================================+==============+=========+
| reliable  | Set RSVP message bundling and summary refresh | | enabled    | enabled |
|           |                                               | | disabled   |         |
+-----------+-----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# refresh-reduction
    dnRouter(cfg-protocols-rsvp-rr)# reliable disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-rr)# no reliable

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
