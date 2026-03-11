ldp rcv-addr-withdraw-delay
---------------------------

**Minimum user role:** operator

Use this command to delay the LDP reaction for an address-withdraw message received from a neighbor. Multiple address-withdraw messages, that are received during the delay period, will be treated together as soon as the delay timer expires.

**Command syntax: rcv-addr-withdraw-delay [delay]**

**Command mode:** config

**Hierarchies**

- protocols ldp 

**Note**

- A value of 0 means there is no delay and LDP will react immediately to any received address-withdraw.

.. - Delay timer is per ldp neighbor

.. - No command return delay to default value

**Parameter table**

+---------------+-------------------------------+-----------+-------------+
|               |                               |           |             |
| Parameter     | Description                   | Range     | Default     |
+===============+===============================+===========+=============+
|               |                               |           |             |
| delay         | The delay period (in seconds) | 0..120    | 0           |
|               |                               |           |             |
|               |                               |           |             |
+---------------+-------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# rcv-addr-withdraw-delay 10

**Removing Configuration**

To return the delay timer to the default value:
::

	dnRouter(cfg-protocols-ldp)# no rcv-addr-withdraw-delay

.. **Help line:** Sets the LDP delay upon receive address-withdraw.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.1      | Command introduced    |
+-----------+-----------------------+