services ethernet-oam link-fault-management profile link-monitoring event-threshold
-----------------------------------------------------------------------------------

**Minimum user role:** operator

To configure thresholds to trigger local RX/TX link events:

**Command syntax: event-threshold [event-type] [threshold]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile link-monitoring

**Parameter table**

+------------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter  | Description                                                                      | Range             | Default |
+============+==================================================================================+===================+=========+
| event-type | The type of threshold event for which this list entry is specifying the          | | symbol-period   | \-      |
|            | configuration.                                                                   | | frame-period    |         |
|            |                                                                                  | | frame-error     |         |
|            |                                                                                  | | frame-seconds   |         |
+------------+----------------------------------------------------------------------------------+-------------------+---------+
| threshold  | The threshold value to use when determining whether to generate an event given   | 1-4294967295      | \-      |
|            | the number of errors that occurred in a given window. The units depend on the    |                   |         |
|            | threshold type as follows:                                                       |                   |         |
|            | Symbol Period: number of errored symbols                                         |                   |         |
|            | Frame Error: number of errored frames                                            |                   |         |
|            | Frame Period: number of errored frames                                           |                   |         |
|            | Frame Seconds: number of seconds containing at least 1 frame error               |                   |         |
+------------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# link-monitoring
    dnRouter(cfg-lfm-profile-lm)# event-threshold symbol-period 100


**Removing Configuration**

To delete a certain threshold:
::

    dnRouter(cfg-lfm-profile-lm)# # no event-threshold symbol-period

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
