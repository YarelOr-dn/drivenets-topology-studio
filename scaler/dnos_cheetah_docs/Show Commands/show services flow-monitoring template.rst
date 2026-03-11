show services flow-monitoring template
--------------------------------------

**Minimum user role:** viewer

To show a flow-monitoring template configuration:

**Command syntax: show services flow-monitoring template [template]**

**Command mode:** operational



**Parameter table**

+-----------+---------------------------------------+-------+---------+
| Parameter | Description                           | Range | Default |
+===========+=======================================+=======+=========+
| template  | Any existing flow-monitoring template | \-    | \-      |
+-----------+---------------------------------------+-------+---------+

**Example**
::

	dnRouter# show services flow-monitoring template myTemplate
	   Template name: myTemplate
	   Template type: IPv4
	   Template-ID: 256
	   Exporter-profile: myExporter
	   Cache Max Entries: 300,000
	   Active Timeout Interval: 3600 sec
	   Idle Timeout Interval: 15 sec

.. **Help line:** show flow-monitoring template configuration.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

