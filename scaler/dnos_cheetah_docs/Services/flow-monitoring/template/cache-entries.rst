services flow-monitoring template cache-entries
-----------------------------------------------

**Minimum user role:** operator

Cached flows are stored in the flow-cache table in the NCP's local CPU. The table can store up to 8,000,000 flows. When you configure multiple flow-monitoring templates, you can limit the number of cached flows for each template.

The maximum cache size per NCP is 8,000,000 entries. If multiple templates are configured with a maximum cache-entries value of 8,000,000, the cache tables for the different templates will compete on the same cache budget on a first-come-first-served basis.

To limit the number of cached flows for the specified template:

**Command syntax: cache-entries [cache-entries]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring template

**Parameter table**

+---------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter     | Description                                                                      | Range        | Default |
+===============+==================================================================================+==============+=========+
| cache-entries | This parameter configures the maximum number of Flows in the Cache, which is the | 1000-8000000 | 65535   |
|               | maximum number of Flows that can be measured simultaneously. The Monitoring      |              |         |
|               | Device MUST ensure that sufficient resources are available to store the          |              |         |
|               | configured maximum number of Flows. If the maximum number of Flows is measured,  |              |         |
|               | an additional Flow can be measured only if an existing entry is removed.         |              |         |
|               | However, traffic that pertains to existing Flows can continue to be measured.    |              |         |
+---------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate
    dnRouter(cfg-srv-flow-monitoring-myTemplate)# cache-entries 300000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-flow-monitoring-myTemplate)# no cache-entries

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
