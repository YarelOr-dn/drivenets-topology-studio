protocols rsvp tunnel weight
----------------------------

**Minimum user role:** operator

Set tunnel weight for unequal load-balancing when working with weighted-ecmp . 
For "tunnel-bw" weight will be per tunnel bw in kbps
To configure the weight for the rsvp tunnel:

**Command syntax: weight [weight]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------------------------+-----------+
| Parameter | Description                                                                      | Range                     | Default   |
+===========+==================================================================================+===========================+===========+
| weight    | configure the tunnel weight to be used for unequal rsvp tunnels multi-path       | 1..4294967295 | tunnel-bw | tunnel-bw |
|           | load-balancing                                                                   |                           |           |
+-----------+----------------------------------------------------------------------------------+---------------------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# weight 1500

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# weight tunnel-bw


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no weight

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
