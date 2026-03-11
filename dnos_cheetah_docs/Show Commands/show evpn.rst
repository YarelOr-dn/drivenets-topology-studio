show evpn 
---------

**Minimum user role:** operator

To show the detailed information of an EVPN database.

**Command syntax: show evpn** instance [evpn-name]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-name          | The name of the EVPN instance           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-name  will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the information for all the EVPN instances.


**Example**
::

    dnRouter# show evpn instance evpn1

    EVPN: evpn1
        EVI ID : 2
        Number of neighbors  : 2
        Number of interfaces : 1

        | Associated interfaces   | State   / Forwarding State         | Uptime              | Actual Local Homing Type    | Learned MACs   |
        +-------------------------+------------------------------------+---------------------+-----------------------------+----------------+
        | ge400-0/0/10.1001       | up / forwarding-all                | 4 days, 23:34:14    | multi-homed-all-active      | 0              |

        (I) - DF Election Highest Preference, Invert Preference is enabled for this interface.

.. **Help line:** show the database information of the EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+