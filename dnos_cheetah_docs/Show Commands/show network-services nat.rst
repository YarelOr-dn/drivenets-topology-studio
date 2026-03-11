show network-services nat
-------------------------

**Minimum user role:** operator

To show all the configured NAT instances.

**Command syntax: show network-services nat** [nat-instance]

**Command mode:** operational

**Parameter table:**

+---------------+-----------------------+--------------+---------------+
| Parameter     | Description           | Values       | Default value |
+===============+=======================+==============+===============+
| nat-instance  | NAT instance name     | String       | \-            |
+---------------+-----------------------+--------------+---------------+

**Note:**

- Specifying a user-configured NAT instance-name will display the specified NAT instance configuration.

- Specifying no instance-name, will result in the listing of all configured NAT instances.

**Example**
::

        dnRouter# show network-services nat

        | NAT Instance   | Internal Interface | External Interface |
        |----------------+--------------------+--------------------|
        | nat-att-pepsi  | nat-0              | nat-1              |
        | nat-att-boa    | nat-2              | nat-3              |



        dnRouter# show network-services nat nat-att-pepsi

        Internal Interface: nat-0
         VLAN: 1000
         Resource: nat-resource-1
        External Interface: nat-1
         VLAN: 2000
        Resource: nat-resource-2
        Timers:
         TCP-timeout: 120 seconds
         UDP-timeout: 120 seconds
         ICMP-timeout: 120 seconds
         Other-timeout: 120 seconds


.. **Help line:** show NAT instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+
