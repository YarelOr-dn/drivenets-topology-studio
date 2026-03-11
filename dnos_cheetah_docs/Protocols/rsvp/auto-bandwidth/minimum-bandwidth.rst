protocols rsvp auto-bandwidth minimum-bandwidth
-----------------------------------------------

**Minimum user role:** operator

A new requested bandwidth reservation is always within the configured minimum and maximum limits. So if the sampled average rate is greater than the configured maximum, the requested bandwidth will be for the set maximum limit. Similarly, if the sampled average rate is lower than the configured minimum, the requested bandwidth will be for the configured minimum limit. A change to the minimum-bandwidth configuration will take effect on the next sampling. To configure the minimum limit:

**Command syntax: minimum-bandwidth [bandwidth]** [units]

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
-  The minimum-bandwidth value must be lower or equal to maximum-bandwidth

.. -  'no minimum-bandwidth' - return bandwidth to its default value

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| bandwidth | tunnel bandwidth                                                                 | 0-4294967295 | 0       |
+-----------+----------------------------------------------------------------------------------+--------------+---------+
| units     | The units used for minimum-bandwidth. If you do not specify the unit, mpbs will  | | kbps       | kbps    |
|           | be used.                                                                         | | mbps       |         |
|           |                                                                                  | | gbps       |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# minimum-bandwidth 10

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# minimum-bandwidth 10000 kbps


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no minimum-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
