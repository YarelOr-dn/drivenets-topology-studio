protocols rsvp auto-bandwidth maximum-bandwidth
-----------------------------------------------

**Minimum user role:** operator

A new requested bandwidth reservation is always within the configured minimum and maximum limits. So if the sampled average rate is greater than the configured maximum, the requested bandwidth will be for the set maximum limit. Similarly, if the sampled average rate is lower than the configured minimum, the requested bandwidth will be for the configured minimum limit. A change to the maximum-bandwidth configuration will take effect on the next sampling. To configure the maximum limit:

**Command syntax: maximum-bandwidth [bandwidth]** [units]

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Note**
-  The minimum-bandwidth value must be lower or equal to maximum-bandwidth

.. -  'no maximum-bandwidth' - return bandwidth to its default value

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+------------+
| Parameter | Description                                                                      | Range        | Default    |
+===========+==================================================================================+==============+============+
| bandwidth | tunnel bandwidth                                                                 | 0-4294967295 | 4194303000 |
+-----------+----------------------------------------------------------------------------------+--------------+------------+
| units     | The units used for maximum-bandwidth. If you do not specify the unit, mpbs will  | | kbps       | kbps       |
|           | be used.                                                                         | | mbps       |            |
|           |                                                                                  | | gbps       |            |
+-----------+----------------------------------------------------------------------------------+--------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# maximum-bandwidth 10000000

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# maximum-bandwidth 1000 gbps


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no maximum-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
