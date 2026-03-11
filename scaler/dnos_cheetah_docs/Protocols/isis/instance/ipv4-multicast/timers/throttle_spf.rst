protocols isis instance address-family ipv4-multicast timers throttle spf
-------------------------------------------------------------------------

**Minimum user role:** operator

IS-IS throttling of shortest path first (SPF) calculations for a given IS-IS address-family topology
delay - time to wait between getting a spf trigger event (for example receiving LSP packet) until running spf calculation
min-holdtime - minimum interval for two consecutive spf runs
max-holdtime - maximum time between consecutive spf runs
throttle algorithm - exponentially increase min-holdtime between spf calculations as long as receiving spf trigger events. if for 2 x max-holdtime duration no spf trigger event happened return min-holdtime to its initial configured value.
Configuration apply for all isis levels


**Command syntax: throttle spf {delay [delay], min-holdtime [min-holdtime], max-holdtime [max-holdtime]}**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast timers

**Note**
- Configuration is per IS-IS address-family topology, When working with Single topology SPF of ipv6-unicast address-family isn't running.
- at least one optional parameter must be configured
- must delay <= min-holdtime <= max-holdtime
- must min-holdtime <= max-holdtime


**Parameter table**

+--------------+-----------------------------------+----------+---------+
| Parameter    | Description                       | Range    | Default |
+==============+===================================+==========+=========+
| delay        | level 2 throttle-spf delay        | 0-600000 | 0       |
+--------------+-----------------------------------+----------+---------+
| min-holdtime | level 2 throttle-spf min-holdtime | 0-600000 | 5       |
+--------------+-----------------------------------+----------+---------+
| max-holdtime | level 2 throttle-spf max-holdtime | 0-600000 | 5000    |
+--------------+-----------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# timers
    dnRouter(cfg-inst-afi-timers)# throttle spf delay 10 min-holdtime 15 max-holdtime 6000
    dnRouter(cfg-inst-afi-timers)# throttle spf max-holdtime 6600 delay 12
    dnRouter(cfg-inst-afi-timers)# throttle spf min-holdtime 20


**Removing Configuration**

To revert delay to default value:
::

    dnRouter(cfg-isis-inst-afi)# no throttle spf delay

To revert min-holdtime to deafult value:
::

    dnRouter(cfg-isis-inst-afi)# no throttle spf min-holdtime

To revert max-holdtime to deafult value:
::

    dnRouter(cfg-isis-inst-afi)# no throttle spf max-holdtime

To revert all parameters to deafult value:
::

    dnRouter(cfg-isis-inst-afi)# no throttle spf max-holdtime

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
