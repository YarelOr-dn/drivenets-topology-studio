protocols rsvp auto-bandwidth underflow-threshold limit
-------------------------------------------------------

**Minimum user role:** operator

After establishing a tunnel LSP, we recommend to delay the next tunnel optimization in order to allow the network to stabilize and for the IGP-TE to converge.
To configure a delay between optimization attempts of sequential tunnels in the optimization queue:

**Command syntax: limit [limit]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth underflow-threshold
- protocols rsvp tunnel auto-bandwidth underflow-threshold
- protocols rsvp auto-mesh tunnel-template auto-bandwidth underflow-threshold

**Note**
-  You may set a new limit while optimization is running. The new delay will take effect at the next tunnel optimization.

.. -  no limit - return delay to its default value

**Parameter table**

+-----------+------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                            | Range | Default |
+===========+========================================================================+=======+=========+
| limit     | the amount of consecutive sampling-interval in which overflow happened | 1-10  | 1       |
+-----------+------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# limit 1


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
