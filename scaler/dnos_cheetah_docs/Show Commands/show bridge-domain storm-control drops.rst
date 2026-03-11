show bridge-domain storm-control drops
--------------------------------------

**Minimum user role:** viewer

To display the number of dropped packets on Bridge-Domain services due to the storm-control metering.

**Command syntax: show bridge-domain storm-control drops**  [instance-name]

**Command mode:** operational

.. **Note**

**Parameter table**

+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter      | Description                                             | Range                                                                                                                                                                                                                                                         | Default |
+================+=========================================================+===============================================================================================================================================================================================================================================================+=========+
| instance-name  | The configured Bridge Domain instance name.             | string 1..255                                                                                                                                                                                                                                                 | \-      |
+----------------+---------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+


**Example**
::

    show bridge-domain storm-control drops

    Bridge-Domain: bd

        Number of local AC interfaces: 1
        | Interface   | Dropped Storm Control Packets (Pkts / Rate pps)   |
        |-------------+---------------------------------------------------|
        | ge100-0/0/3 | 2343 / 0                                          |


    Bridge-Domain: test

        Number of local AC interfaces: 2
        | Interface   | Dropped Storm Control Packets (Pkts / Rate pps)   |
        |-------------+---------------------------------------------------|
        | ge100-0/0/0 | 1567 / 0                                          |
        | ge100-0/0/1 | 2211 / 0


.. **Help line:** show bridge-domain storm-control drops

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+