protocols segment-routing mpls path dynamic no-stack-compression
----------------------------------------------------------------

**Minimum user role:** operator

By default, the calculated dynamic path will utilize node-sid or anycast-sids to leverage transit LSR multi-path forwarding.
Usage of node-sid or anycast-sids is limited to cases where the LSR forwarding per given SID topology matches the required dynamic path constraints.
With no-stack-compression, the operator has the option to enforce the calculated dynamic path representation as a fully strict hop by hop adjacency-sid list.
To enable no-stack-compression:


**Command syntax: no-stack-compression [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic

**Note**

- If the dynamic path has no configured constraint or only has the algorithm constraint, the provided path is expected to be a single SID matching the policy destination pre required algorithm (i.e the spf / strict-spf / flex-algo route).

- The provided path SID solution will also include any uloop, lfa or ti-lfa solution that exists for the spf / strict-spf / flex-algo route.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | do not compress calculated path to use node/anycast-sids and provide paths as    | | enabled    | disabled |
|             | multiple full strict adj-sid label stacks                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# no-stack-compression enabled


**Removing Configuration**

To return no-stack-compression to default behavior:
::

    dnRouter(cfg-mpls-path-dynamic)# no no-stack-compression

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
