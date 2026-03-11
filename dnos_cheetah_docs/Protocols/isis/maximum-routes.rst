protocols isis maximum-routes
-----------------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. The scale is aggregated across all isis instances and address-families.

To set thresholds on IS-IS routes:

**Command syntax: maximum-routes [max-routes]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- There is no strict limitation on the number of IS-IS adjacencies that can be formed.

- When a threshold is crossed (max-routes or threshold), a single system-event notification is generated.

- When a threshold is cleared (max-routes or threshold), a single system-event notification is generated.

**Parameter table**

+------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                                      | Range        | Default |
+============+==================================================================================+==============+=========+
| max-routes | The maximum number of IS-IS routes you want in the RIB. When this threshold is   | 1-4294967295 | 32000   |
|            | crossed, a single system-event notification is generated. You will not be        |              |         |
|            | notified again.                                                                  |              |         |
|            | 0 means no limit; a system-event will not be generated.                          |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+
| threshold  | A percentage (%) of max-routes to give you advance notice that the number of     | 1-100        | 75      |
|            | IS-IS routes in the RIB is reaching the maximum level. When this threshold is    |              |         |
|            | crossed, a system-event notification is generated. You will not be notified      |              |         |
|            | again.                                                                           |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# maximum-routes 15000 threshold 80

In the above example, the maximum number of IS-IS routes in the RIB is set to 15,000 and the threshold is set to 80%. This means that when the number of IS-IS routes in the RIB reaches 12,000, a system-event notification will be generated that the 80% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 15,000.


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-isis)# no maximum-routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
