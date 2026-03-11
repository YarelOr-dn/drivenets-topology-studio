protocols rsvp path-selection
-----------------------------

**Minimum user role:** operator

This command sets the type of metric cspf should consider when finding an LSP path. The metric types are:

•	te-metric - The interface traffic-engineering metric, signaled as part of the traffic-engineering information by the igp protocol

•	igp-metric - The interface igp-metric.

To configure the metric-type:

**Command syntax: path-selection [path-selection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+----------------+-------------------------------------------------------------+----------------+-----------+
| Parameter      | Description                                                 | Range          | Default   |
+================+=============================================================+================+===========+
| path-selection | Set which metric should cspf consider whan finding lsp path | | te-metric    | te-metric |
|                |                                                             | | igp-metric   |           |
+----------------+-------------------------------------------------------------+----------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# path-selection igp-metric


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no path-selection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
