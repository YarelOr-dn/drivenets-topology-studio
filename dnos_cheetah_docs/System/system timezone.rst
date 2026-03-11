system timezone
---------------

**Minimum user role:** operator
System timezone provides a full sync for dates and times between all the containers in all the clusters or Standalone components.

To set the system time-zone, use the following command:

**Command syntax: timezone [timezone]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Changing the time-zone will affect the displayed system uptime, logs, traces, debug files, and CLI transactions.

.. - No system timezone return timezone parameter to default value (UTC)

**Parameter table**

+-----------+-----------------------------------+---------------------------------------------------------------+---------+
| Parameter | Description                       | Range                                                         | Default |
+===========+===================================+===============================================================+=========+
| timezone  | Sets the time-zone for the system | Linux time-zone list, use the 'tab' help key to view the list | UTC     |
+-----------+-----------------------------------+---------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# timezone UTC



**Removing Configuration**

To revert the timezone to default:
::

	dnRouter(cfg-system)# no timezone

.. **Help line:** Configure system timezone

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 5.1.0   | Command introduced                                      |
+---------+---------------------------------------------------------+
| 6.0     | Applied new hierarchy                                   |
+---------+---------------------------------------------------------+
| 13.1    | Added timezone configuration for formats other than UTC |
+---------+---------------------------------------------------------+
