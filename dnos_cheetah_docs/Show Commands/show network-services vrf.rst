show network-services vrf
-------------------------

**Minimum user role:** operator

To show VRF instances. By default, the device is configured with default, mgmt0, mgmt-ncc-0 and mgmt-ncc-1 (these are all reserved values).

**Command syntax: show network-services vrf** {[vrf-name] | all}

**Command mode:** operational

**Parameter table:**

+-----------+-----------------------+--------------+---------------+
| Parameter | Description           | Values       | Default value |
+===========+=======================+==============+===============+
| vrf-name  | The name of the VRF   | String | all | \-            |
+-----------+-----------------------+--------------+---------------+

**Note:**

- Specifying a user-configured vrf-name will display the specified VRF's configuration

- Specifying 'all' will result in the listing of all configured VRFs

**Example**
::

	dnRouter# show network-services vrf

	| Name           |
	|----------------|
	| default        |
	| mgmt0          |
	| mgmt-ncc-0     |
	| mgmt-ncc-1     |
	| my_vrf-2       |


	dnRouter# show network-services vrf my_vrf-2

	VRF: my_vrf-2
		VRF ID: 5, Type: VRF-lite
		Description: Customer_VRF_Test
		Associated interfaces:
			bundle-2
			bundle-3.100
			ge100-2/0/1
			ge100-3/0/7.22
			ge100-4/0/2
			lo0


	dnRouter# show network-services vrf default

	VRF: default
		VRF ID: 0, Type: VRF-lite
		Description:
		Associated interfaces:
			bundle-1160
			ge100-2/0/11
			ge100-3/0/7.26
			ge100-3/0/9
			lo1
		Maximum routes: 2550000, Threshold: 75% (1912500)


	dnRouter# show network-services vrf all

	VRF: default
		VRF ID: 0, Type: VRF-lite
		Description:
		Associated interfaces:
			bundle-1160
			ge100-2/0/11
			ge100-3/0/7.26
			ge100-3/0/9
			lo1
		Maximum routes: 2550000, Threshold: 75% (1912500)

	VRF: my_vrf-2
		VRF ID: 5, Type: VRF-lite
		Description: Customer_VRF_Test
		Associated interfaces:
			bundle-2
			bundle-3.100
			ge100-2/0/1
			ge100-3/0/7.22
			ge100-4/0/2
			lo0

	VRF: mgmt0
		VRF ID: 8001, Type: VRF-lite
		Description:
		Associated interfaces:
			mgmt0

	VRF: mgmt-ncc-0
		VRF ID: 8002, Type: VRF-lite
		Description:
		Associated interfaces:
			mgmt-ncc-0

	VRF: mgmt-ncc-1
		VRF ID: 8003, Type: VRF-lite
		Description:
		Associated interfaces:
			mgmt-ncc-1


.. **Help line:** show VRF instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
