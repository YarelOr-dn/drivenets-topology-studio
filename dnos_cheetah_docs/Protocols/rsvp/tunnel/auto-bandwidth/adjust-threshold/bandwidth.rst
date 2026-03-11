protocols rsvp tunnel auto-bandwidth adjust-threshold bandwidth
---------------------------------------------------------------

**Minimum user role:** operator

After establishing a tunnel LSP, we recommend to delay the next tunnel optimization in order to allow the network to stabilize and for the IGP-TE to converge.
To configure a delay between optimization attempts of sequential tunnels in the optimization queue:

**Command syntax: bandwidth [bandwidth]** [units]

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel auto-bandwidth adjust-threshold
- protocols rsvp auto-bandwidth adjust-threshold
- protocols rsvp auto-mesh tunnel-template auto-bandwidth adjust-threshold

**Note**
-  You may set a new bandwidth while optimization is running. The new delay will take effect at the next tunnel optimization.

.. -  no bandwidth - return delay to its default value

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| bandwidth | perform bandwidth adjustments if traffic rate is more/less than current          | 0-4294967295 | \-      |
|           | bandwidth allocation                                                             |              |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+
| units     | The units used for bandwidth. If you do not specify the unit, mpbs will be used. | | kbps       | kbps    |
|           |                                                                                  | | mbps       |         |
|           |                                                                                  | | gbps       |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# bandwidth 1


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
