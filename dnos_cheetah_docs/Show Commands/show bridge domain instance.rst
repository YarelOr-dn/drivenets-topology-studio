show bridge-domain instance
----------------------------

**Minimum user role:** operator

To show the detailed information of a Bridge-Domain instance.

**Command syntax: show bridge-domain instance [bridge-domain-name]**

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| bridge-domain-name | The name of the Bridge Domain           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying a bridge-domain-name will display the information of the specified Bridge-Domain.

- Specifying 'all' will result in the listing of the detailed information for all BD instances.


**Example**
::

    dnRouter# show bridge-domain instance bd1

    Bridge-Domain: bd1
       Description: BRIDGE_DOMAIN_SERVICE_1
       Admin State: Up


       Mac Table
       ==========
       mac-learning: enabled
       mac-table-limit: 100000 entries
       mac-table-aging-time: 320 seconds
       current-number-of-mac-entries: 79

       Number of local AC interfaces: 2

       Interface         |    State   |     Uptime       |   MAC Entries |
       ------------------+------------+------------------+---------------+
       bundle-262.2547   |    Up      | 2 days, 14:53:28 |       23      |
       ge100-0/0/2       |    Down    | 0 days, 00:00:00 |       56      |



    dnRouter# show bridge-domain instance all

    Bridge-Domain: bd1
       Description: BRIDGE_DOMAIN_SERVICE_1
       Admin State: Up


       Mac Table
       ==========
       mac-learning: enabled
       mac-table-limit: 100000 entries
       mac-table-aging-time: 320 seconds
       current-number-of-mac-entries: 79

       Number of local AC interfaces: 2

       Interface         |    State   |     Uptime       |   MAC Entries |
       ------------------+------------+------------------+---------------+
       bundle-262.2547   |    Up      | 2 days, 14:53:28 |       23      |
       ge100-0/0/2       |    Down    | 0 days, 00:00:00 |       56      |


    Bridge-Domain: bd2
       Description: BRIDGE_DOMAIN_SERVICE_2
       Admin State: Up


       Mac Table
       ==========
       mac-learning: enabled
       mac-table-limit: 100000 entries
       mac-table-aging-time: 60 seconds
       current-number-of-mac-entries: 214

       Number of local AC interfaces: 3

       Interface         |    State   |     Uptime        |   MAC Entries |
       ------------------+------------+-------------------+---------------+
       bundle-27.44      |    Up      | 1 days,  14:53:28 |       185     |
       ge100-0/0/2.326   |    Down    | 0 days,  00:00:00 |       0       |
       ge100-0/0/5.3     |    Up      | 125 days, 06:0:00 |       29      |


   Bridge-Domain: bd3-irb
       Description: BRIDGE_DOMAIN_SERVICE_3 with IRB
       Admin State: Up

       Associated IRB interface: irb1 
                State: Up


       Mac Table
       ==========
       mac-learning: enabled
       mac-table-limit: 20000 entries
       mac-table-aging-time: 60 seconds
       current-number-of-mac-entries: 465

       Number of local AC interfaces: 2

       Interface         |    State   |     Uptime        |   MAC Entries |
       ------------------+------------+-------------------+---------------+
       bundle-23.77      |    Up      | 1 days,  19:35:06 |       185     |
       ge100-0/0/2.43    |    Down    | 0 days,  00:00:00 |       0       |
         

.. **Help line:** show information for Bridge Domain instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 17.2    | Command introduced                  |
+---------+-------------------------------------+