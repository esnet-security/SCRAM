Feature: restrict changing entries
  We do not want users updating a route after it has been added; a change should be a new object.

  Scenario: user can't update a route
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And we add the entry 192.0.2.208
    And we update the entry 192.0.2.208 to 192.0.2.209
    Then we get a 405 status code
    And the number of entrys is 1
#    And 192.0.2.208 is announced by block translators
#    And 192.0.2.209 is not announced by block translators
