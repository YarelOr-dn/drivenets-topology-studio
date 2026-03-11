protocols rsvp auto-bypass admin-state
--------------------------------------

**Minimum user role:** operator

You can enable or disable tunnel optimization globally for all tunnel types, or per tunnel. To enable/disable tunnel optimization per tunnel, see "rsvp tunnel optimization".
To enable/disable tunnel optimization globally:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass

**Note**
- Disabling the optimization while optimization is running will stop all running optimization attempts.

.. -  'no admin-state' - return admin-state to default value

**Parameter table**

+-------------+----------------------------+--------------+---------+
| Parameter   | Description                | Range        | Default |
+=============+============================+==============+=========+
| admin-state | enable auto-bypass tunnels | | enabled    | enabled |
|             |                            | | disabled   |         |
+-------------+----------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
