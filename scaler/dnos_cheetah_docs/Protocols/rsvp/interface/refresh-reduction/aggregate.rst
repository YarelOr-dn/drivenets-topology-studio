protocols rsvp interface refresh-reduction aggregate
----------------------------------------------------

**Minimum user role:** operator

Use the aggregate attribute to bundle standard RSVP messages (i.e.. Path, PathErr, Resv, ResvTear, ResvErr, ResvConf, ACK) into a single RSVP message. Doing so improves message processing overhead.
To enable or disable message aggregation for the interface:

**Command syntax: aggregate [aggregate]**

**Command mode:** config

**Hierarchies**

- protocols rsvp interface refresh-reduction

**Parameter table**

+-----------+-----------------------------------------------+--------------+---------+
| Parameter | Description                                   | Range        | Default |
+===========+===============================================+==============+=========+
| aggregate | Set RSVP message bundling and summary refresh | | enabled    | \-      |
|           |                                               | | disabled   |         |
+-----------+-----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)# refresh-reduction
    dnRouter(cfg-rsvp-if-rr)# aggregate disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-rsvp-if-rr)# no aggregate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
