services flow-monitoring cache-rate-limit
-----------------------------------------

**Minimum user role:** operator

You can limit the rate for exporting flow-records from the cache during flush or age-out events.

Any sampled packets beyond 200,000 pps will be disregarded by the control plane and counted as dropped. Note, that this limit is per exporter.

To configure the rate limit:

**Command syntax: cache-rate-limit [cache-rate-limit]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+------------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter        | Description                                                                      | Range    | Default |
+==================+==================================================================================+==========+=========+
| cache-rate-limit | flow records export rate limit from flow cache table during flush or massive     | 0-200000 | 200000  |
|                  | ageout events                                                                    |          |         |
+------------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# cache-rate-limit 100000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-port-mirroring)# no cache-rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
