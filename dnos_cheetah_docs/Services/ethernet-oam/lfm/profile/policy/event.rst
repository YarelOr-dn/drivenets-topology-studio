services ethernet-oam link-fault-management profile policy event action
-----------------------------------------------------------------------

**Minimum user role:** operator

To configure a policy for the 802.3ah EFM OAM events:

**Command syntax: event [event-type] action [action]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile policy

**Parameter table**

+------------+-------------------------------------------------------------------+--------------------------+---------+
| Parameter  | Description                                                       | Range                    | Default |
+============+===================================================================+==========================+=========+
| event-type | Type of event that occurred.                                      | | adjacency-loss-event   | \-      |
|            |                                                                   | | dying-gasp-event       |         |
|            |                                                                   | | threshold-event        |         |
+------------+-------------------------------------------------------------------+--------------------------+---------+
| action     | The action to execute upon the occurence of the triggering event. | | oper-down              | ignore  |
|            |                                                                   | | ignore                 |         |
+------------+-------------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# policy
    dnRouter(cfg-lfm-profile-policies)# event adjacency-loss action oper-down

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# policy
    dnRouter(cfg-lfm-profile-policies)# event dying-gasp action ignore

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# policy
    dnRouter(cfg-lfm-profile-policies)# event threshold-event action oper-down


**Removing Configuration**

To delete a policy:
::

    dnRouter(cfg-lfm-profile-policies)# no event adjacency-loss

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
