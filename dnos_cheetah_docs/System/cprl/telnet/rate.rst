system cprl telnet rate
-----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Telnet protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl telnet

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
    dnRouter(cfg-system-cprl)# telnet
    dnRouter(cfg-system-cprl-telnet)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Telnet protocol:
::

    dnRouter(cfg-system-cprl-telnet)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
