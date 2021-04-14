Feature: restrict changing entries
  We do not want users updating a route after it has been added; a change should be a new object.

  Scenario: user can't update a route
    When we're logged in
    And we add the IP 1.2.3.4
    And we update the IP 1.2.3.4 to 1.2.3.5
    Then we get a 405 status code
    And the number of IPs is 1
