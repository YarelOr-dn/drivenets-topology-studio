services flow-monitoring sampler-profile rate 1-out-of
------------------------------------------------------

**Minimum user role:** operator

The sampling of traffic uses a sequential rate algorithm. The rate defines which packet in a sequence of packets to sample. For example, a sampling rate of 1:2 (1-out-of-2) means that every other packet is sampled; a rate of 1:5 means that every fifth packet is sampled, etc.

To define the rate at which the traffic is sampled:

**Command syntax: rate 1-out-of [sample-rate]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring sampler-profile

**Note**
- A sample rate of 1:1 is possible. However, the total number of sampled packets that can be sent to the local CPU per NCP is limited to 200,000 packets per second.

**Parameter table**

+-------------+----------------------+---------+---------+
| Parameter   | Description          | Range   | Default |
+=============+======================+=========+=========+
| sample-rate | packet sampling rate | 1-65535 | 2048    |
+-------------+----------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# sampler-profile mySampler
    dnRouter(cfg-srv-flow-monitoring-mySampler)# rate 1-out-of 2048


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-mySampler)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
