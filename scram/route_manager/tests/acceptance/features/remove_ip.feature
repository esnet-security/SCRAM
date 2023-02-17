Feature: remove a network
  Users can remove a v4 and v6 network

  Scenario: unauthenticated users get a 403
    Given a client without block authorization
    When we add the entry 127.0.0.1
    Then we get a 403 status code

  Scenario Outline: removing a nonexistant IP returns a 204 (the client should not have to worry about it)
    When we're logged in
    And we remove the entry <PK>
    Then we get a 204 status code

    Examples: Made Up Primary Key
      | PK        |
      | 1         |
      | 9.9.9.9   |

  Scenario: removing an existing IP returns a 204
    Given a client with block authorization
    When we're logged in
    And we add the entry 1.2.3.4/32
    And we remove the entry 1.2.3.4/32
    Then we get a 204 status code
    And the number of entrys is 0
