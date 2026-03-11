routing-options maximum-routes
------------------------------

**Minimum user role:** operator

When BGP is connected to multiple external peers it is difficult to control what these peers advertise. Routing polices are used to control what is accepted from a peer. In cases where peers advertise a large amount of prefixes (more than the system can handle), the system is expected to be able to contain this load and once the issue is handled to resume the normal operation.

BGP protection can prevent this on the neighbor level, however if the scale is from multiple neighbors, there is no limitation in BGP and RIB and this scale can overload the whole system.

You can control the size of the RIB by setting thresholds to generate system event notifications. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary.

RIB routes are limited in a 1:1 ratio between IPv4 and IPv6, for IGP routes, and a 4:1 ratio between IPv4 and IPv6 for other route types. When setting the maximum-route maximum value to 2,550,000, the RIB will install up to 2,025,000 IPv4 routes and 525,000 IPv6 routes to the FIB. By default, limits IGP routes to 50,000 and will not install IGP routes above this limit.

To configure RIB size thresholds:

**Command syntax: maximum-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Set the maximum-routes to 0 to disable maximum-routes limitation and system-events.

- The thresholds are for IPv4 and IPv6 combined.

- When the number of routes drops below a threshold, a system-event notification is generated.

.. - Reconfiguration behavior:

	*    when "maximum" is reconfigured, resulting that current routes number is now below the new maximum value. over-the-limit routes will be installed upto new maximum value.
	*    when "maximum" is reconfigured, resulting that current routes number is now above the new maximum value. only new routes will be blocked from installment. No affect on existing routes that were already installed


	- no command returns maximum & threshold to their default values

**Parameter table**

+------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+---------+
| Parameter  | Description                                                                                                                                                                                                                             | Range                | Default |
+============+=========================================================================================================================================================================================================================================+======================+=========+
| max-routes | The maximum number of routes you want in the RIB.                                                                                                                                                                                       | 0, 100000..20000000  | 2550000 |
|            | Set maximum-routes to 0 to disable the maximum-routes limitation and system events.                                                                                                                                                     |                      |         |
+------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+---------+
| threshold  | A percentage (%) of max-routes to give you advance notice that the number of routes in the RIB is reaching the maximum level. When this threshold is crossed, a system-event notification is generated. You will not be notified again. | 1..100               | 75      |
+------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+---------+

Although new routes will still be accepted even if the max-routes limit is reached, you should remove any undesired local routes (e.g. unnecessary static routes), check if all BGP neighbors are justified and verify that the correct policies are used upon receiving a system-event notification that a threshold has been crossed.

In the example, the maximum number of routes in the RIB is set to 1,500,000 and the threshold is set to 70%. This means that when the number of routes in the RIB reaches 1,050,000, a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of routes reaches 1,500,000.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# maximum-routes 2000000

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# maximum-routes 1500000 threshold 70
	
	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# maximum-routes 0



**Removing Configuration**

To revert to the default values:
::

	dnRouter(cfg-routing-option)# no maximum-routes

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 13.2    | Updated command parameter ranges |
+---------+----------------------------------+


