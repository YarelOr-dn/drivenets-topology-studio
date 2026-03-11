protocols ospf instance area interface delay-normalization
----------------------------------------------------------

**Minimum user role:** operator

Performance monitoring (PM) measures various link characteristics like packet loss, delay and jitter. Such characteristics can be used by OSPF as a metric for Flexible Algorithm computation. Low latency routing, using dynamic delay measurement, is one of the primary use cases for the Flexible Algorithm technology.
The delay is measured in microseconds. If the delay values are taken as measured and used as link metrics during the OSPF topology computation, some valid ECMP paths might be unused because of the negligible difference in the link delay.
The Delay Normalization feature computes a normalized delay value and uses the normalized value instead. This value is advertised and used as a metric during the Flexible Algorithm computation.
The normalization is performed when the delay is received from the delay measurement component. When the next value is received, it is normalized and compared to the previous saved normalized value. If the values are different, then the LSA generation is triggered.
The following formula is used to calculate the normalized value:
- Dm: measured Delay
- Int: configured normalized Interval
- Off: configured normalized Offset (must be less than the normalized interval Int)
- Dn: normalized Delay
- a = Dm / Int (rounded down)
- b = a * Int + Off
If the measured delay (Dm) is less than or equal to b, then the normalized delay (Dn) is equal to b. Otherwise, Dn is b + Int.
To configure OSPFv2 interface delay normalization and enter the delay normalization configuration mode:

**Command syntax: delay-normalization**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface ge100-0/0/0
    dnRouter(cfg-ospf-area-interface)# delay-normalization
    dnRouter(cfg-area-interface-normalization)#


**Removing Configuration**

To revert all delay normalization configuration to its default values:
::

    dnRouter(cfg-ospf-area-interface)# no delay-normalization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
