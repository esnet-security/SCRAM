Feature: block with BGP
  Users can block routes via BGP

  Scenario: We can block a v4 IP
    When we add 192.0.2.4/32 to the block list
    Then 192.0.2.4 is blocked
    And 192.0.2.5 is unblocked

  Scenario: We can block a v6 IP
    When we add 2001:DB8:A::/64 to the block list
    Then 2001:DB8:A:: is blocked
    And baba:: is unblocked

  Scenario: We can block, then unblock a v4 IP
    When we add 192.0.2.4/32 to the block list
    And we delete 192.0.2.4/32 from the block list
    Then 192.0.2.4 is unblocked

  Scenario: We can block, then unblock a v6 IP
    When we add 2001:DB8:B::/64 to the block list
    And we delete 2001:DB8:B::/64 from the block list
    Then 2001:DB8:B:: is unblocked
