network-services vrf instance protocols bgp bestpath delay
----------------------------------------------------------

**Minimum user role:** operator

Upon initialization following a restart, the BGP process waits for the configured amount of time before starting to send its updates. During this delay, the router listens to updates coming from the peers without responding. When the peers finish sending updates, or when the timer expires, the BGP calculates the best path for each route and starts advertising to its peers. The best path delay improves convergence because by waiting for all the information before calculating the best paths, less advertisements are required.

The best path delay command sets the maximum time to wait after the first neighbor is established until the BGP starts calculating best paths and sending out advertisements:

**Command syntax: bestpath delay [bestpath-delay]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| bestpath-delay | Set delay for the first bestpath calculation to all updates to be received from  | 0-3600 | 120     |
|                | all peers                                                                        |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath delay 10


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no bestpath delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
