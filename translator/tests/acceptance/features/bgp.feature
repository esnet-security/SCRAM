Feature: block with BGP
  Users can block routes via BGP

  Scenario: We can block a v4 IP
    When we add 1.2.3.4/32 to the block list
    Then 1.2.3.4 is blocked
    And 1.2.3.5 is unblocked

  Scenario: We can block a v6 IP
    When we add f00::/64 to the block list
    Then f00:: is blocked
    And baba:: is unblocked

  Scenario: We can block, then unblock a v4 IP
    When we add 1.2.3.4/32 to the block list
    And we delete 1.2.3.4/32 from the block list
    Then 1.2.3.4 is unblocked

  Scenario: We can block, then unblock a v6 IP
    When we add f00::/64 to the block list
    And we delete f00::/64 from the block list
    Then f00:: is unblocked
