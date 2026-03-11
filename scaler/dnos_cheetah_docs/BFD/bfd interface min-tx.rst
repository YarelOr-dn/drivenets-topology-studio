bfd interface min-tx
--------------------

**Minimum user role:** operator

The minimum transmission interval is the desired time between consecutive transmissions of BFD packets. Upon negotiation with the remote 

To configure the transmission rate of BFD packets:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

**Note**

- All micro BFD sessions for the given bundle member will use the same session parameters

- Due to hardware limitation, maximum supported transmit rate is 1700msec, and negotiated transmit interval higher than 1700msec will result in actual transmit rate of 1700msec.

.. - the no command returns to default values

**Parameter table**

+---------------+--------------------------------------------------------------+------------+-------------+
|               |                                                              |            |             |
| Parameter     | Description                                                  | Range      | Default     |
+===============+==============================================================+============+=============+
|               |                                                              |            |             |
| min-tx        | The interval (in msec) between transmissions of BFD packets. | 5..1700    | 300         |
|               |                                                              |            |             |
+---------------+--------------------------------------------------------------+------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# min-tx 100


**Removing Configuration**

To return to the default value: 
::

	dnRouter(cfg-protocols-bfd-if)# no min-tx

**Command History**

+-------------+-------------------------------------+
|             |                                     |
| Release     | Modification                        |
+=============+=====================================+
|             |                                     |
| 11.2        | Command introduced                  |
+-------------+-------------------------------------+
|             |                                     |
| 15.1        | Added support for 5msec interval    |
+-------------+-------------------------------------+