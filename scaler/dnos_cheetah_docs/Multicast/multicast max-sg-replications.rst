multicast max-sg-replications
-----------------------------

**Minimum user role:** operator

You can limit the number of Multicast group join requests (S,G replications) and once the limit is met, any new request that arrives will be dropped. In addition, you can define a threshold (1-100%) to generate an alert once the threshold is met.

To configure the maximum number of IP multicast replications per all (S,G) requests:

**Command syntax: max-sg-replications [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols multicast

**Note**

- Threshold - the percentage of the value specified by **maximum**

- The 'no-max-sg-replications' command reverts the both the sg-replications and threshold to their default values.'no max-sg-replications' command reverts back both the sg-replications and threshold to their default values.

**Parameter table**

+-----------+-------------------------------------------------------------+------------+---------+
| Parameter | Description                                                 | Range      | Default |
+===========+=============================================================+============+=========+
| maximum   | The maximum number of (S,G) replications (entries)          | 1..220,000 | 220,000 |
+-----------+-------------------------------------------------------------+------------+---------+
| threshold | The percentage of the value specified by the maximum-states | 1..100     | 75      |
+-----------+-------------------------------------------------------------+------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# multicast
	dnRouter(cfg-multicast)# max-sg-replications 180000
	dnRouter(cfg-multicast)#

	dnRouter# configure
	dnRouter(cfg)# multicast
	dnRouter(cfg-multicast)# max-sg-replications 200000 threshold 90
	dnRouter(cfg-multicast)#

**Removing Configuration**

To remove the limit of Multicast group join requests:
::

	dnRouter(cfg-multicast)# no max-sg-replications

.. **Help line:** Sets the maximum number output replications per all (S,G) groups.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command Introduced |
+---------+--------------------+
