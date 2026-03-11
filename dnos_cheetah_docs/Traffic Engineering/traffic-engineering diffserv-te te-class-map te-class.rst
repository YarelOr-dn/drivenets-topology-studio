traffic-engineering diffserv-te te-class-map te-class
-----------------------------------------------------

**Minimum user role:** operator

The traffic-engineering class is the unique pairing of a class-type with a tunnel priority (see table below for the default TE-class mappings). You can assign a different tunnel priority or class-type for each TE-class, however, the same pairing cannot be assigned to different TE classes.

The default te-class mapping:

+----------+------------+----------+
| TE-Class | Class-Type | Priority |
+==========+============+==========+
| 0        | 0          | 7        |
+----------+------------+----------+
| 1        | 1          | 7        |
+----------+------------+----------+
| 2        | unused     |          |
+----------+------------+----------+
| 3        | unused     |          |
+----------+------------+----------+
| 4        | 0          | 0        |
+----------+------------+----------+
| 5        | 1          | 0        |
+----------+------------+----------+
| 6        | unused     |          |
+----------+------------+----------+
| 7        | unused     |          |
+----------+------------+----------+

For a tunnel to be established, there must be a valid mapping for both tunnel {class-type, setup-priority} and tunnel {class-type, hold-priority}. If the tunnel priority and class-type pair isn't mapped to a te-class the commit will fail with an error message.

If a tunnel matches two te-classes (one for setup priority and one for hold priority), the tunnel's te-class will be based on the hold-priority.


To map class-type and tunnel priority to each TE class:


**Command syntax: te-class [te-class] class-type {{ [class-type] priority [priority]} \| unused}**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te te-class-map

**Note**

- When changing a te-class mapping , if the new configuration conflicts with existing tunnels, the new configuration will not affect the existing tunnels. In this case, you should clear the tunnels manually to apply the change.

-  Diff-serv TE mode is IETF


**Parameter table**

+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|               |                                                                                                                                                              |                 |             |
| Parameter     | Description                                                                                                                                                  | Range           | Default     |
+===============+==============================================================================================================================================================+=================+=============+
|               |                                                                                                                                                              |                 |             |
| te-class      | A paired class-type and tunnel priority                                                                                                                      | 0..7            | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|               |                                                                                                                                                              |                 |             |
| class-type    | A set of traffic flows that have the same set of   bandwidth constraints. When set to "unused", you cannot set   priority and the class-type is unusable.    | 0..1, unused    | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|               |                                                                                                                                                              |                 |             |
| priority      | The preemption priority for the class-type. You   cannot set a priority for class-type "unused".                                                             | 0..7            | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|               |                                                                                                                                                              |                 |             |
| unused        | Use for reserving the TE-class for future   assignment.                                                                                                      | \-              | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# te-class-map
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 0 class-type 0 priority 1
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 1 class-type 1 priority 1
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 2 class-type 1 priority 2
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 3 class-type 1 priority 3
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 4 class-type 0 priority 4
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 5 class-type 0 priority 5
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 6 class-type 0 priority 6
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 7 class-type 0 priority 7


	dnRouter(cfg-mpls-te-diffserv)# te-class-map
	dnRouter(cfg-te-diffserv-te-class-map)# te-class 3 class-type unused

**Removing Configuration**

To revert to the default te-class mapping (for a specific te-class):
::

	dnRouter(cfg-mpls-te-diffserv)# no te-class 5


.. **Help line:**

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 10.0        | Command introduced                      |
+-------------+-----------------------------------------+
|             |                                         |
| 13.0        | Updated   class-type parameter value    |
+-------------+-----------------------------------------+