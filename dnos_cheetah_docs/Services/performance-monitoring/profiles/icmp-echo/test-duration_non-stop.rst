services performance-monitoring profiles icmp-echo test-duration non-stop
-------------------------------------------------------------------------

**Minimum user role:** operator

To set a non-stop test:

**Command syntax: test-duration non-stop {probe-interval [probe-interval], computation-interval [computation-interval]}**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Parameter table**

+----------------------+---------------------------------------------------------+--------+---------+
| Parameter            | Description                                             | Range  | Default |
+======================+=========================================================+========+=========+
| probe-interval       | The interval between subsequent probes in the test.     | 1-255  | 1       |
+----------------------+---------------------------------------------------------+--------+---------+
| computation-interval | Periodic computation interval. Valid for non-stop mode. | 1-3600 | 60      |
+----------------------+---------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# test-duration non-stop probe-interval 60

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# test-duration non-stop probe-interval 2 computation-interval 300

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# test-duration non-stop computation-interval 53


**Removing Configuration**

To return the test duration configuration to default:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no test-duration non-stop

To return the probe interval configuration to default:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no test-duration non-stop probe-interval

To return the computation interval configuration to default:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no test-duration non-stop computation-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
