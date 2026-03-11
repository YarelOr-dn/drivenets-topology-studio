network-services vrf instance protocols bgp dynamic-med-interval
----------------------------------------------------------------

**Minimum user role:** operator

When using an egress policy with 'set med igp-cost', any change in the MED attribute is advertised.
To configure a delay in the advertisement of updates:

**Command syntax: dynamic-med-interval [interval]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| interval  | Set delay interval for consecutive updates due to MED attribute change when      | 0-15  | 0       |
|           | using set med igp-cost                                                           |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# dynamic-med-interval 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no dynamic-med-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
