protocols rsvp optimization queue-delay
---------------------------------------

**Minimum user role:** operator

After establishing a tunnel LSP, we recommend to delay the next tunnel optimization in order to allow the network to stabilize and for the IGP-TE to converge.
To configure a delay between optimization attempts of sequential tunnels in the optimization queue:

**Command syntax: queue-delay [queue-delay]**

**Command mode:** config

**Hierarchies**

- protocols rsvp optimization

**Note**
-  You may set a new queue-delay while optimization is running. The new delay will take effect at the next tunnel optimization.

.. -  no queue-delay - return delay to its default value

**Parameter table**

+-------------+--------------------------------------------------------+-------+---------+
| Parameter   | Description                                            | Range | Default |
+=============+========================================================+=======+=========+
| queue-delay | sets delay between consecutive tunnels being optimized | 0-59  | 3       |
+-------------+--------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization
    dnRouter(cfg-protocols-rsvp-optimization)# queue-delay 1


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-optimization)# no queue-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
