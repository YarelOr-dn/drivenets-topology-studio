show network-services evpn
--------------------------

**Minimum user role:** operator

To show EVPN instances.

**Command syntax: show network-services evpn** {[evpn-name] | all}

**Command mode:** operational

**Parameter table:**

+-----------+-----------------------+--------------+---------------+
| Parameter | Description           | Values       | Default value |
+===========+=======================+==============+===============+
| evpn-name | The name of the EVPN  | String | all | \-            |
+-----------+-----------------------+--------------+---------------+

**Note:**

- Specifying an evpn-name will display the specified EVPN's configuration

- Specifying 'all' will result in the listing of all configured EVPNs

**Example**
::

	dnRouter# show network-services evpn

	| Name           |
	|----------------|
	| evpn1          |
	| evpn2          |
	| evpn3          |


	dnRouter# show network-services evpn evpn1

	EVPN: evpn1
		EVI ID: 1
        Description: EVPN Service for Customer-A
        Remote PEs/VTEPS:
            192.168.10.1
            146.76.19.4
        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542


	dnRouter# show network-services evpn all

    EVPN: evpn1
		EVI ID: 1
        Description: EVPN Service for Customer-A
        Remote PEs/VTEPS:
            192.168.10.1
            146.76.19.4
        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542

     EVPN: evpn2
		EVI ID: 2
        Description: EVPN Service for Customer-B
        Remote PEs/VTEPS:
            178.16.105.11
            132.26.19.4
        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542

.. **Help line:** show VRF instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 17.2    | Command introduced                  |
+---------+-------------------------------------+