services performance-monitoring profiles endpoint-delay test-duration probes
----------------------------------------------------------------------------

**Minimum user role:** operator

To set the duration of each test in probe-count:

**Command syntax: test-duration probes {probe-count [probe-count], probe-interval [probe-interval], repeat-interval [repeat-interval]}**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay

**Parameter table**

+-----------------+-----------------------------------------------------+--------------+---------+
| Parameter       | Description                                         | Range        | Default |
+=================+=====================================================+==============+=========+
| probe-count     | The number of probes in the test.                   | 1-4294967295 | 60      |
+-----------------+-----------------------------------------------------+--------------+---------+
| probe-interval  | The interval between subsequent probes in the test. | 1-255        | 1       |
+-----------------+-----------------------------------------------------+--------------+---------+
| repeat-interval | The interval between subsequent tests.              | 1-4294967295 | 60      |
+-----------------+-----------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# test-duration probes probe-count 60

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# test-duration probes probe-count 100 probe-interval 2 repeat-interval 300

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# test-duration probes probe-interval 53


**Removing Configuration**

To return the test duration configuration to default:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no test-duration probes

To return the probe count configuration to default:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no test-duration probes probe-count

To return the probe interval configuration to default:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no test-duration probes probe-interval

To return the repeat interval configuration to default:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no test-duration probes repeat-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
