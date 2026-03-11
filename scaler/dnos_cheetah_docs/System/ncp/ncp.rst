system ncp
----------

**Minimum user role:** operator

This command caters for both provisioned and for pre-provisioned scenarios:
- Provisioned NCP

    In the provisioned scenario, the cluster's NCPs have already been discovered and have each received a unique identifier (NCP-ID). The administrative state of an automatically provisioned cluster NCP is initially disabled. To enable it, you must enter the NCP's configuration mode using its NCP-ID and model. You can at any time use this command to change its admin-state and/or description.
    In this scenario, the NCP-ID is already mapped to a specific NCP model. If you enter a model that does not match the specific NCP-ID, an error is displayed. If no mismatch is found, you will enter the configuration mode for the NCP.

- Pre-provisioning NCPs

    For pre-provisioning, you configure the cluster's NCPs before physically connecting them, so that when you connect them and power them up, they are discovered with their pre-designated IDs. If you connect an NCP whose model does not match the pre-configured model for this slot, an error is displayed.

To configure an NCP:

**Command syntax: ncp [ncp-id]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt.

- While the NCP model is not required to identify a provisioned NCP, you nevertheless need to specify it as the same command is used to configure NCPs in a pre-provisioning scenario.

- You cannot remove the configuration for a standalone NCP. Although a standalone NCP automatically receives the ID 0, the no ncp 0 command will delete a cluster's NCP, but not a standalone NCP.

**Parameter table**

+-----------+-----------------------------------------------------------------+-------+---------+
| Parameter | Description                                                     | Range | Default |
+===========+=================================================================+=======+=========+
| ncp-id    | The identifier of the NCP. The ID is unique within the cluster. | 0..191|   \-    |
+-----------+-----------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)#


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-system)# no ncp 7

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
