show network-services vrf counters
----------------------------------

**Minimum user role:** operator

**Description:** To display the VRF redirect counters:


**Command syntax: show network-services vrf** counters {[vrf-name] | all}

**Command mode:** operational


..

	**Note**

	- Specifying a user-configured vrf-name displays the redirect counters for the specified VRF

	- Specifying 'all' results in the listing of the counters for all VRFs


**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                                             | Range  | Default |
+===========+=========================================================================================================================+========+=========+
| vrf-name  | Filters the output to display the redirect counters for the specified VRF. Use "All" to list the counters for all VRFs. | String | \-      |
|           |                                                                                                                         | All    |         |
+-----------+-------------------------------------------------------------------------------------------------------------------------+--------+---------+


**Example**
::

	dnRouter# show network-services vrf counters my_vrf-2


	vrf my_vrf_2:
    Redirect forward counters:
      Rx Packets:                     100
      Rx octets:                      10,231

    Redirect drop counters:
      Destination route is null0:     10
      Destination route unreachable:  25
      Chain vrf:                      8

.. **Help line:** show network-services VRF counters [vrf-name]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
