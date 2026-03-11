show network-services bridge-domain
-----------------------------------

**Minimum user role:** operator

To show Bridge-Domain instances.

**Command syntax: show network-services bridge-domain** {[bridge-domain-name] | all}

**Command mode:** operational

**Parameter table:**

+--------------------+--------------------------------+--------------+---------------+
| Parameter          | Description                    | Values       | Default value |
+====================+================================+==============+===============+
| bridge-domain-name | The name of the Bridge Domain  | String | all | \-            |
+--------------------+--------------------------------+--------------+---------------+

**Note:**

- Specifying a bridge-domain-name will display the specified Bridge-Domain's configuration.

- Specifying 'all' will result in the listing of all configured BDs.

**Example**
::

	dnRouter# show network-services bridge-domain

	| Name           |
	|----------------|
	| bd1            |
	| bd2            |
	| bd3            |


	dnRouter# show network-services bridge-domain bd1

	Bridge-Domain: bd1
        Description: Bridge Domain Service for Customer-A
        Admin State: Up

        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542


	dnRouter# show network-services bridge-domain all

    Bridge-Domain: bd1
        Description: Bridge Domain Service for Customer-A
        Admin State: Up

        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542

     Bridge-Domain: bd2
        Description: Bridge Domain Service for Customer-B
        Admin State: Up

        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542

    Bridge-Domain: bd3-irb
        Description: Bridge Domain Service for Customer-C with IRB
        Admin State: Up

        Associated IRB interface:
            irb1

        Associated interfaces:
            bundle-258.2514
            bundle-258.2515
            bundle-258.2516
            bundle-262.2542

.. **Help line:** show Bridge Domain instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 17.2    | Command introduced                  |
+---------+-------------------------------------+