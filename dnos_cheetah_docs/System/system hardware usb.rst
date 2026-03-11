system hardware usb
-------------------

**Minimum user role:** operator

To enter the USB configuration mode:

**Command syntax: system [node-name] [node-id] hardware usb [usb-id]**

**Command mode:** config

**Hierarchies**

- system hardware usb


**Note**

- Notice the change in prompt.

- The command is applicable to any node (NCP, NCC, NCF).

.. - no command returns the usb configuration to its default.

	- First user configured usb id is attached to first operation system assigned id usb.

**Parameter table**

+-----------+---------------------------------------------------+-------+---------+
| Parameter | Description                                       | Range | Default |
+===========+===================================================+=======+=========+
| usb-id    | The identifier of the USB port on the NC element. | 0..5  | \-      |
+-----------+---------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 1
	dnRouter(cfg-system-ncp-1)# hardware usb 0
	dnRouter(cfg-ncp-0-hardware-usb)#



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ncp-0-hardware)#no usb 0

.. **Help line:** configure usb for DNOS cluster nodes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
| 17.1    | Update max usb-id  |
+---------+--------------------+
