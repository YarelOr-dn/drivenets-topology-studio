system hardware usb admin-state
-------------------------------

**Minimum user role:** operator

To enable/disable the USB on a cluster element:

**Command syntax: usb [usb-id] admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system hardware usb


**Note**

- The command is applicable to any node (NCP, NCC, NCF).

.. - Admin-state disabled means unmount usb device.

	- admin-state -applies only after the DNOS software is loaded to the device and is first booted


**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                        | Range    | Default  |
+=============+====================================================================================================+==========+==========+
| admin-state | The administrative state of the USB port. When disabled, you will not be able to use the USB port. | Enabled  | Disabled |
|             |                                                                                                    | Disabled |          |
+-------------+----------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 1
	dnRouter(cfg-system-ncp-1)# hardware usb 0
	dnRouter(cfg-ncp-1-hardware-usb)# admin-state disabled
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-hardware-ncp-usb)# no admin-state

.. **Help line:** configure usb for DNOS cluster nodes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+

