services flow-monitoring template
---------------------------------

**Minimum user role:** operator

A flow monitoring template includes a list of parameters that define how to sample and maintain IP flows for a system. The template defines the following:

-	The type of traffic to monitor (see "services flow-monitoring template type")

-	The size of the flow cache table that maintains the active IP flows (see "services flow-monitoring template cache-entries")

-	How long an active flow can be stored in the flow cache table before it is aged out (see "services flow-monitoring template flow-active-timeout")

-	How long a flow is considered active when no packet is observed (see "services flow-monitoring template flow-idle-timeout")

-	The list of collectors to which IP flow information is exported (see "services flow-monitoring template exporter-profile")

You can create up to 10 different templates per system. Each template can be attached to any data-path interface or sub-interface.

To create a flow-monitoring template:

**Command syntax: template [template]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+-----------+--------------------------------------------------+------------------+---------+
| Parameter | Description                                      | Range            | Default |
+===========+==================================================+==================+=========+
| template  | Reference to the configured name of the template | | string         | \-      |
|           |                                                  | | length 1-255   |         |
+-----------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# template myTemplate


**Removing Configuration**

You cannot delete a template that is attached to an interface. To delete the template, remove the association with the interface before deleting it.
::

    dnRouter(cfg-srv-flow-monitoring)# no template myTemplate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
