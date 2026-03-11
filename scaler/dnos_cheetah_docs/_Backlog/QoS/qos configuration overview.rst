QoS configuration overview
--------------------------

A qos policy is a set of rules. A rule is a policy composed of traffic-class to match and list of actions to perform if traffic matches the traffic pattern defined in the traffic-class.

Rules in a policy defines the order of execution. Rules id is a number, rules are executed in ascending order.

Here is the general structure of a policy:

Qos policy <policy-name>

rule 1

description "rule description"

match traffic-class <traffic-class-map>

actions

<action-1>

<action-2>

rule 2

. . .

rule-default

action

<action-1>

<action-2>

**rule-default**

Implicitly created for each policy. Traffic that doesn't match any of the preceding rules will match the default rule.

**Hierarchical QoS configuration**

[STRIKEOUT:Allows enforcement per aggregate interface/vlan (customer) in addition to enforcement of QoS policy per class within the customer.]

[STRIKEOUT:The hierarchical action commands supported on parent (aggregate interface) are police (ingress) and shape (egress)]

[STRIKEOUT:Parent policy consist of rule-default only.]

[STRIKEOUT:Examples:]

[STRIKEOUT:qos policy MyChildPolicy1_out]

[STRIKEOUT:rule 1]

[STRIKEOUT:description "myTrafficClass1"]

[STRIKEOUT:match traffic-class myTrafficMap1]

[STRIKEOUT:actions]

[STRIKEOUT:queue af bandwidth 40 percent]

[STRIKEOUT:rule-default]

[STRIKEOUT:actions]

[STRIKEOUT:queue af bandwidth 10 percent]

[STRIKEOUT:qos policy MyParentPolicy1_out]

[STRIKEOUT:rule-default]

[STRIKEOUT:actions]

[STRIKEOUT:shape rate 40 percent]

[STRIKEOUT:policy-child MyChildPolicy1]

[STRIKEOUT:qos policy MyChildPolicy1_in]

[STRIKEOUT:rule 1]

[STRIKEOUT:match traffic-class myTrafficMap2]

[STRIKEOUT:actions]

[STRIKEOUT:police]

[STRIKEOUT:committed-rate 40 percent committed-burst 100msec]

[STRIKEOUT:peak-rate 60 percent]

[STRIKEOUT:peak-burst 400msec]

[STRIKEOUT:yellow-action set dscp 5]

[STRIKEOUT:set qos-tag 4]

[STRIKEOUT:set red-tag 1]

[STRIKEOUT:qos policy MyParentPolicy1_in]

[STRIKEOUT:rule-default]

[STRIKEOUT:actions]

[STRIKEOUT:police]

[STRIKEOUT:committed-rate 40 percent]

[STRIKEOUT:policy-child MyChildPolicy1]

**Traffic-class map**

Traffic-class-map defines a traffic class by allowing to match on packet fields.

By default traffic-class match is defined as "match-any", i.e traffic will hit the rule if any of the match fields is met.

If "match-all" is configured for the traffic-class-map, then all conditions must be met (currently not supported).

Qos traffic-map traffiClassMap1 match-any

Dscp 24, 26

Qos traffic-map traffiClassMap2 match-any

Mpls exp 7

Precedence 7

The following match fields are supported

+------------------+-------------+------------+
| **Match field**  | **Ingress** | **Egress** |
+------------------+-------------+------------+
| Dscp             | +           |            |
+------------------+-------------+------------+
| Precedence       | +           |            |
+------------------+-------------+------------+
| Mpls exp topmost | +           |            |
+------------------+-------------+------------+
| qos-tag          |             | +          |
+------------------+-------------+------------+
| 802.1p           | +           |            |
+------------------+-------------+------------+

Dscp and precedence field relevant for ipv4 or ipv6

Examples:

Qos traffic-map match-any traffiClassMap1

Dscp 24, 26

Qos traffic-map match-any traffiClassMap2

Mpls exp 7

Precedence 7

**Qos actions**

Following are the qos actions that are supported in qos policy

+-------------------------+-------------+------------+
| **Action \  interface** | **Ingress** | **Egress** |
+-------------------------+-------------+------------+
| Set dscp                | +           | +          |
+-------------------------+-------------+------------+
| Set precedence          | +           | +          |
+-------------------------+-------------+------------+
| Set mpls-exp-topmost    | +           | +          |
+-------------------------+-------------+------------+
| Set qos-tag             | +           |            |
+-------------------------+-------------+------------+
| Set red-tag             | +           |            |
+-------------------------+-------------+------------+
| Set 802.1p              |             | +          |
+-------------------------+-------------+------------+
| Queue                   |             | +          |
+-------------------------+-------------+------------+

**Egress scheduling**

Aggregate rate of a policy is the shape rate configured on parent policy or the physical rate of the port (if shape is not configured).

The rates and guaranteed bandwidth of the queues will be relative to the aggregate bandwidth

The scheduler has 4 forwarding classes that are served in strict priority in the following order: super-expedited-forwarding (super-ef), expedited-forwarding (ef), assured-forwarding (af[STRIKEOUT:) and then best-effort (be)]. As long as there is traffic on queue matching a forwarding class, and the queue hasn't reached its max-bandwidth, the scheduler will not serve queues in lower priority forwarding classes

A policy on interface can have up to 6 queues:

-  1 super-ef queue

-  1 ef queue

-  4 af queue

-  [STRIKEOUT:1 be queue]

a queue inherits its properties from the forwarding-class it belongs to.

Properties are: scheduling priority, [STRIKEOUT:queue size and wred profile] parameters.

[STRIKEOUT:(see default-wred-profile, default-queue-size-profile).]

*Super-ef* and *ef* queues configured with max-bandwidth to avoid starvation of lower priory queues.

[STRIKEOUT:Note that If max-bandwidth is not set for those queues, they can exploit 100% of the port bandwidth, therefore it is recommended to configure upper limit.]

The *bandwidth* command on af queue sets its relative bandwidth in the forwarding-class

If bandwidth is not set, the queue will get an equal quanta of remaining bandwidth on the af forwarding-class in that policy.

Remaining bandwidth is calculated as following:

(100 -- sum of bandwidth in *af* queues) / # of *af* queues

for example:

qos policy MyChildPolicy1_out

rule 1

match traffic-class myTrafficMap1

actions

queue super-ef max-bandwidth 20 percent

rule 2

match traffic-class myTrafficMap2

actions

queue ef max-bandwidth 30 percent

rule 3

match traffic-class myTrafficMap3

actions

queue af bandwidth 40 percent

rule 4

match traffic-class myTrafficMap4

actions

queue af bandwidth 40 percent

rule 5

match traffic-class myTrafficMap5

actions

queue af

rule 6

match traffic-class myTrafficMap6

actions

queue af

in the above example, the remaining bandwidth on the af forwarding class is 20%

(100 - 40 - 40 ). Since there are 4 queues in total , the 20% will split into 5% for each queue.

queue af1 will get 45%

queue af2 will get 45%

queue af3 will get 5%

queue af4 will get 5%

How to determine the guaranteed bandwidth on the af queues?

The guaranteed bandwidth of the af forwarding class is calculated as the aggregate rate (shape rate or physical rate) minus the max-bandwidth configured on higher priority forwarding-classes.

In the example above:

The guaranteed bandwidth of the af forwarding class is 50% of the aggregate rate of the interface:

100 - 20 (max-bandwidth of super-ef) - 30 (max bandwidth of ef )

Within the forwarding class, each queue will get a min bandwidth calculated as percentage of the guaranteed bandwidth of the af forwarding class.

In the above example, when guaranteed bandwidth of the af is 50%:

Queue af1 will have a guaranteed bandwidth of 22.5% from the aggregate traffic

Queue af2 will have a guaranteed bandwidth of 22.5% from the aggregate traffic

Queue af3 will have a guaranteed bandwidth of 2.5% from the aggregate traffic

Queue af4 will have a guaranteed bandwidth of 2.5% from the aggregate traffic

**Queue limit**

[STRIKEOUT:Queue limit is defined globally per forwarding class. (see scheduler for explanations on forwarding classes)]

[STRIKEOUT:Example:]

[STRIKEOUT:Qos default-queue-size-profile]

[STRIKEOUT:Super-Ef queue-max 50 packets]

[STRIKEOUT:Ef queue-max 50 packets]

[STRIKEOUT:Af queue-max 100 packets]

[STRIKEOUT:Be queue-max 1000 packets]

**Wred**

WRED profiles are configured globally per af traffic forwarding class.

i.e. each af forwarding classes can have up to  **2 curves**.

The matching of traffic to wred-profile is done by the red tag:

Traffic marked with red-tag 0 will be subject to drop profile of curve-0 (DP = 0, Green color), traffic marked with red-tag 1 will be subject to drop profile of curve-1 (DP = 1, Yellow color).

Marking of red-tag is done in ingress policies. This red-tag is used to select the wred profile on VOQ.

Default values:

All curves are set to "no random drops". (i.e. min and max are set to queue-max-size)

example for global wred config

qos

wred-profile

my_af1_profile

af curve-0min1max100

af curve-1min20max100

!

my_af2_profile

af curve-0min10max100

af curve-1min40max100

!

!

**Locally generated packets**

Each protocol management is responsible to configure its priority hence to determine where it will be queued according to QoS policy.
