Feature: block with BGP
  Users can block routes via BGP

  Scenario: We can block an IP
    When we add 1.2.3.4/32 to the block list
    Then 1.2.3.4 is blocked
