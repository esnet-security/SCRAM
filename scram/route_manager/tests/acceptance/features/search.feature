Feature: Test our search bar
  We need to make sure search works as expected

  Scenario Outline: Searching for a valid CIDR works
    Given a client with block authorization
    When we're logged in
    And we add the entry <ip>
    And we search for <ip>
    Then we get a 200 status code

    Examples: IPs
    | ip                 |
    | 192.0.2.168        |
    | 2001:DB8:9508::1   |

  Scenario Outline: Searching for an invalid CIDR sends a 400
    Given a client with block authorization
    When we're logged in
    And we search for <ip>
    Then we get a 400 status code

  Examples: IPs
    | ip    |
    | " "   |
    | asdf  |
