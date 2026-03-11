protocols segment-routing mpls policy path lock
-----------------------------------------------

**Minimum user role:** operator

Set the lock timer (in seconds) over a given candidate path to prevent path replacement in when a better candidate path is found valid.
The operator may use lock logic to prevent frequent policy path changes.
- The value '0' (default behavior) result is that the candidate path is replaced from installed as active path as soon as a better candidate path is found valid.
- The values '1..65535' results are that the candidate path is replaced from installed as active, only once it was used for the duration of the lock timer or once found to be invalid.
- The value 'until-invalid' result is that the candidate path is replaced only once found to be invalid.


To configure the lock timer for sr-te path:


**Command syntax: lock [lock]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy path

**Note**

- The lock does not prevent a backup path from becoming active if the active path fails.

- The lock timer starts upon path installed as active. The path update does not reset the lock timer.

- Reconfig of the lock timer only applies to the next time the lock is set.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| lock      | Set a lock over a given candidate path to prevent path replacement in case a     | \-    | 0       |
|           | better candidate path found valid to use                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# path PATH_1 priority 5
    dnRouter(cfg-mpls-policy-path)# lock 30

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# path PATH_1 priority 5
    dnRouter(cfg-mpls-policy-path)# lock until-invalid


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-sr-mpls-policy)# no lock

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
