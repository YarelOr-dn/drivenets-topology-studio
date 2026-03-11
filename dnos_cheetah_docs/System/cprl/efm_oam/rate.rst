system cprl efm-oam rate
------------------------

**Minimum user role:** operator

To set the rate limit of the control traffic for the 802.3ah EFM OAM protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl efm-oam

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 1000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# efm-oam
    dnRouter(cfg-system-cprl-efm-oam)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the 802.3ah EFM OAM protocol:
::

    dnRouter(cfg-system-cprl-efm-oam)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
