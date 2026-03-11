routing-options fec-statistics
------------------------------

**Minimum user role:** operator

To configure the mpls fec-statistics operation mode:

**Command syntax: fec-statistics [fec-statistics]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Default behavior is to counter per in-label and egress-interface for supported protocols

- Configuration applies to new installed FIB mpls routes only

**Parameter table**

+----------------+------------------------------------------------------------+-------------------------------+---------------------------+
| Parameter      | Description                                                | Range                         | Default                   |
+================+============================================================+===============================+===========================+
| fec-statistics | Configuration for mpls fec-statistics of in-label counters | | in-label-egress-interface   | in-label-egress-interface |
|                |                                                            | | disabled                    |                           |
+----------------+------------------------------------------------------------+-------------------------------+---------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# fec-statistics disabled


**Removing Configuration**

To revert the behavior to its default:
::

    dnRouter(cfg-routing-option)# no fec-statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
