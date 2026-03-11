protocols rsvp administrative-distance
--------------------------------------

**Minimum user role:** operator

The command sets the RSVP administrative-distance. This allows you to control the way RSVP tunnels take preference over other protocols (for example, LDP) in RIB tables.
To define the RSVP administrative-distance:

**Command syntax: administrative-distance [administrative-distance]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
-  An administrative distance of 255 will cause the route to be removed from the forwarding table and will not be used.

.. -  When reconfiguring administrative-distance, user should run clear rsvp tunnel, new administrative-distance values will only apply to new rsvp tunnels installed in RIB

.. - no command return to default value

**Parameter table**

+-------------------------+----------------------------------+-------+---------+
| Parameter               | Description                      | Range | Default |
+=========================+==================================+=======+=========+
| administrative-distance | administrative distance for RSVP | 1-255 | 100     |
+-------------------------+----------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# administrative-distance 90


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no administrative-distance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
