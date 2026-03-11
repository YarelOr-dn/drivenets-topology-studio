system ssh server vrf
---------------------

**Minimum user role:** operator

Allows to define separate SSH client-lists and admin-states per VRF (in-band default, in-band non-default and out-of-band)

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Note**

- Notice the change in prompt.

- vrf definition level is introduced for attaching client-list.

- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

- client-list configuration configured under VRF mgmt0 will be implicitly attached and applied on the host out-of-band interfaces (mgmt-ncc-0 and mgmt-ncc-1)

- no command deletes the configuration under the specific vrf.

- validation is required to fail commit if more than 3 non-default VRFs are configured in general

**Parameter table**

+-----------+----------------------+------------------+---------+
| Parameter | Description          | Range            | Default |
+===========+======================+==================+=========+
| vrf-name  | The name of the vrf. | | string         | \-      |
|           |                      | | length 1-255   |         |
+-----------+----------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)#
    dnRouter(cfg-system-ssh-server)#  vrf default
    dnRouter(cfg-ssh-server-vrf)#
    dnRouter(cfg-system-ssh-server)# vrf mgmt0
    dnRouter(cfg-ssh-server-vrf)#
    dnRouter(cfg-system-ssh-server)# vrf my_vrf
    dnRouter(cfg-ssh-server-vrf)#


**Removing Configuration**

To delete the configuration under the non-default specific vrf:
::

    dnRouter(cfg-system-ssh-server)# no vrf my_vrf

For VRF default and mgmt0 no command will reset the configuration::
::

    dnRouter(cfg-system-ssh-server)# no vrf default

**Command History**

+---------+---------------------+
| Release | Modification        |
+=========+=====================+
| 13.1    | Command introduced  |
+---------+---------------------+
| 19.1    | Added NDVRF Support |
+---------+---------------------+
