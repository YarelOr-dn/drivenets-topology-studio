static maximum-routes
---------------------

**Minimum user role:** operator

You can control the size of the RIB by setting thresholds to generate system event notifications for static routes. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary.

Although new routes will still be accepted even if the max-routes limit is reached, you should remove any undesired routes upon receiving a system-event notification that a threshold has been crossed. 

To configure RIB size thresholds for static routes:

**Command syntax: maximum-routes [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols static

**Note**

- The thresholds are for generating system-events only. There is no limit on the number of static routes that you can configure. 

- The thresholds are for IPv4 and IPv6 routes combined.

- When the threshold is cleared, a single system-event notification is generated.

- There is no limitation on the number of static routes that you can configure.


**Parameter table**

+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                                                                                                                                                                         |             |             |
| Parameter     | Description                                                                                                                                                                                                                                             | Range       | Default     |
+===============+=========================================================================================================================================================================================================================================================+=============+=============+
|               |                                                                                                                                                                                                                                                         |             |             |
| max-routes    | The maximum number of static routes you want in   the RIB. When this threshold is crossed, a single system-event notification   is generated. You will not be notified again.                                                                           | 1..65535    | 2000        |
|               |                                                                                                                                                                                                                                                         |             |             |
|               | 0 means no limit; a system-event will not be   generated.                                                                                                                                                                                               |             |             |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                                                                                                                                                                         |             |             |
| threshold     | A percentage (%) of max-routes to give you   advance notice that the number of static routes in the RIB is reaching the   maximum level. When this threshold is crossed, a system-event notification is   generated. You will not be notified again.    | 1..100      | 75          |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**

In this example, the maximum number of static routes in the RIB is set to 1,000 and the threshold is set to 70%. This means that when the number of routes in the RIB reaches 700, a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 1,000.
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# maximum-routes 1000 threshold 70

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-rsvp)# no maximum-routes


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+