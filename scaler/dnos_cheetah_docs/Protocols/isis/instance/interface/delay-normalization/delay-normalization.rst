protocols isis instance interface delay-normalization
-----------------------------------------------------

**Minimum user role:** operator

Performance monitoring (PM) measures various link characteristics like packet loss, delay and jitter. Such characteristics can be used by IS-IS as a metric for flexible algorithm computation. Low latency routing using dynamic delay measurement is one of the primary use cases for flexible algorithm technology.
Delay is measured in microseconds. If delay values are taken as measured and used as link metrics during the IS-IS topology computation, some valid ECMP paths might be unused because of the negligible difference in the link delay.
The Delay Normalization feature computes a normalized delay value and uses the normalized value instead. This value is advertised and used as a metric during the flexible algorithm computation.
The normalization is performed when the delay is received from the delay measurement component. When the next value is received, it is normalized and compared to the previous saved normalized value. If the values are different, then the LSP generation is triggered.

The following formula is used to calculate the normalized value:

  Dm – measured delay

  Int – configured normalized interval

  Off – configured normalized offset (must be less than the normalized interval Int)

  Dn – normalized delay

  a = Dm / Int (rounded down)

  b = a * Int + Off

If the measured delay (Dm) is less than or equal to b, then the normalized delay (Dn) is equal to b. Otherwise, Dn is b + Int.


To configure IS-IS interface delay normalization and enter the delay normalization configuration mode:

**Command syntax: delay-normalization**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# delay-normalization
    dnRouter(cfg-inst-if-normalization)#


**Removing Configuration**

To revert all delay normalization configuration to its default values:
::

    dnRouter(cfg-isis-inst-if)# no delay-normalization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
