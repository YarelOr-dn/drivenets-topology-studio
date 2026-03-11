protocols segment-routing mpls flex-algo advertise-definition
-------------------------------------------------------------

**Minimum user role:** operator

To guarantee the loop-free forwarding for paths computed for a particular flex-algorithm, all the routers that are configured to participate in a particular flex-algorithm, must agree on the definition of the flex-algorithm.
The flex-algorithm definition is a set of contstraints from which the IGP topology is derived and how the path calculation is expected.
Different routers in the Flex-Algo domain can advertise a flex-algorithm definition, according to tie-breaking logic definition of a specific router that is selected to be used 
among all participating routers.
To configure a Flex-Algo definition profile with constraint set and enter its configuration mode:

**Command syntax: advertise-definition [Flex-Algo Definition Name]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo

**Parameter table**

+---------------------------+----------------------------------------+------------------+---------+
| Parameter                 | Description                            | Range            | Default |
+===========================+========================================+==================+=========+
| Flex-Algo Definition Name | flex algorithm definition profile name | | string         | \-      |
|                           |                                        | | length 1-255   |         |
+---------------------------+----------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)#


**Removing Configuration**

To remove the advertise-definition configuration:
::

    dnRouter(cfg-sr-mpls-flex-algo)# no advertise-definition MIN_DELAY_130

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
