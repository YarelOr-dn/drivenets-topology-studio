protocols rsvp auto-mesh tunnel-template auto-bandwidth adjust-threshold percent
--------------------------------------------------------------------------------

**Minimum user role:** operator

After establishing a tunnel LSP, we recommend to delay the next tunnel optimization in order to allow the network to stabilize and for the IGP-TE to converge.
To configure a delay between optimization attempts of sequential tunnels in the optimization queue:

**Command syntax: percent [percent]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template auto-bandwidth adjust-threshold
- protocols rsvp auto-bandwidth adjust-threshold
- protocols rsvp tunnel auto-bandwidth adjust-threshold

**Note**
-  You may set a new percent while optimization is running. The new delay will take effect at the next tunnel optimization.

.. -  no percent - return delay to its default value

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| percent   | perform bandwidth adjustments if traffic rate is more/less than current          | 0-100 | \-      |
|           | bandwidth allocation by percent%                                                 |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# percent 1


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no percent

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
