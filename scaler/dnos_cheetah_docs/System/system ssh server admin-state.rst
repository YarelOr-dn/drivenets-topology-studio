system ssh server admin-state
-----------------------------

**Minimum user role:** operator

Configure the state of the SSH server on the system.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Note**

- Changing the server admin-state to "disabled" will immediately terminate any active session.

- no command returns the state to default.

- Once disabled, only console access is provided.

- Active sessions are immediately disconnected upon configuration of "disable".

- Only new sessions can not be established

- SSH server supports connections on the following interfaces

- physical

- sub-interface(physical.vlan, bundle.vlan)

- loopback

- mgmt

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                         | Range        | Default |
+=============+=====================================================================+==============+=========+
| admin-state | admin-state of ssh-server per system, the global admin-state switch | | enabled    | enabled |
|             |                                                                     | | disabled   |         |
+-------------+---------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# admin-state disabled


**Removing Configuration**

To revert the ssh server admin-state to default:
::

    dnRouter(cfg-system-ssh-server)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
