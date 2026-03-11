protocols rsvp tunnel bypass primary path-selection
---------------------------------------------------

**Minimum user role:** operator

Set which type of metric cspf should consider when finding an LSP path.

The metric-types are:

- te-metric - The interface traffic-engineering metric, signaled as part of the traffic-engineering information by the igp protocol.

- igp-metric - The interface igp-metric.

To configure the metric-type:

**Command syntax: path-selection [path-selection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary

**Parameter table**

+----------------+-------------------------------------------------------------+--------------+---------+
| Parameter      | Description                                                 | Range        | Default |
+================+=============================================================+==============+=========+
| path-selection | Set which metric should cspf consider whan finding lsp path | te-metric    | \-      |
|                |                                                             | igp-metric   |         |
+----------------+-------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# path-selection igp-metric

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# path-selection te-metric

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# path-selection igp-metric

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# primary
    dnRouter(cfg-auto-mesh-temp-primary)# path-selection igp-metric

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-auto-bypass-primary)# path-selection igp-metric


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no path-selection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
