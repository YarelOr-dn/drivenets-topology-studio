system ssh server vrf admin-state
---------------------------------

**Minimum user role:** operator

Configure the state of the SSH server on the system.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ssh server vrf

**Note**

- Changing the server admin-state to "disabled" will immediately terminate any active session

- Once disabled, only console access is provided.

- Active sessions are immediately disconnected upon configuration of "disable".

- Only new sessions can not be established

- SSH server supports connections on the following interfaces

- physical

- sub-interface(physical.vlan, bundle.vlan)

- loopback

- mgmt

- Validation - fail commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.

**Parameter table**

+-------------+-----------------------------------+--------------+---------+
| Parameter   | Description                       | Range        | Default |
+=============+===================================+==============+=========+
| admin-state | admin-state of ssh-server per VRF | | enabled    | enabled |
|             |                                   | | disabled   |         |
+-------------+-----------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# admin-state disabled
    dnRouter(cfg-ssh)# server vrf mgmt0
    dnRouter(cfg-ssh-server-vrf)# admin-state enabled
    dnRouter(cfg-ssh-server-vrf)#
    dnRouter(cfg-ssh)# server vrf my_vrf
    dnRouter(cfg-ssh-server-vrf)# admin-state disabled
    dnRouter(cfg-ssh-server-vrf)#


**Removing Configuration**

To revert the admin-state to default:
::

    dnRouter(cfg-system-ssh-server)# no admin-state

**Command History**

+---------+---------------------+
| Release | Modification        |
+=========+=====================+
| 13.1    | Command introduced  |
+---------+---------------------+
| 19.1    | Added NDVRF Support |
+---------+---------------------+
