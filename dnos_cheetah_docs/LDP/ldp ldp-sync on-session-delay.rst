ldp ldp-sync on-session-delay
-----------------------------

**Minimum user role:** operator

The MPLS LDP-IGP synchronization feature provides a means to synchronize LDP and IGPs to minimize MPLS packet loss. When an IGP adjacency is established on a link but LDP IGP synchronization is not yet achieved or is lost, the IGP advertises the max-metric on that link. LDP-sync is always enabled in LDP. Also, all OSPF interfaces (except loopbacks) are enabled for LDP sync.
To configure LDP-IGP synchronization:

**Command syntax: ldp-sync on-session-delay [on-session-delay]**

**Command mode:** config

**Hierarchies**

- protocols ldp 

**Note**

- LDP sync is always enabled in LDP either with no delay or with configured delay. 

.. - LDP sync is only effective if the related IGP has LDP Sync enabled on the related interface.

.. - LDP synchronization is not supported during graceful restart.

.. - 'no ldp-sync' or 'no ldp-sync on-session-delay' commands reverts the LDP Sync on-session-delay to the default value.

**Parameter table**

+---------------------+--------------------------------------------------------------------------------------------------+-------------------+-------------------+
|                     |                                                                                                  |                   |                   |
| Parameter           | Description                                                                                      | Range             | Default value     |
+=====================+==================================================================================================+===================+===================+
|                     |                                                                                                  |                   |                   |
| on-session-delay    | The amount of time to wait (in seconds) before notifying if the LDP interface is synchronized    | 1..300 seconds    | 15 seconds        |
+---------------------+--------------------------------------------------------------------------------------------------+-------------------+-------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# ldp-sync on-session-delay 50

**Removing Configuration**

To revert the delay configuraiton to default:
::

	dnRouter(cfg-protocols-ldp)# no ldp-sync on-session-delay

	dnRouter(cfg-protocols-ldp)# no ldp-sync

.. **Help line:** Sets the LDP sync per session delay.

**Command History**

+-------------+------------------------------------------------------+
|             |                                                      |
| Release     | Modification                                         |
+=============+======================================================+
|             |                                                      |
| 6.0         | Command introduced                                   |
+-------------+------------------------------------------------------+
|             |                                                      |
| 13.0        | Command syntax changed from on-proc to on-session    |
+-------------+------------------------------------------------------+