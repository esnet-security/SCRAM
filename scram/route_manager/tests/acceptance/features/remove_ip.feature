Feature: remove a network
  Users can remove a v4 and v6 network

  Scenario: unauthenticated users get a 403
    When we add the entry 127.0.0.1
    Then we get a 403 status code

  Scenario Outline: removing a nonexistant IP returns a 204 (the client should not have to worry about it)
    When we're logged in
    And we remove the entry <PK>
    Then we get a 204 status code

    Examples: Made Up Primary Key
      | PK  |
      | 1   |


  Scenario Outline: removing an existing IP returns a 204
    When we're logged in
    And we add the entry <IP>
    And we remove the entry <PK>
    Then we get a 204 status code
    And the number of entrys is 0

    Examples: v4 IPs
      | PK | IP            |
      | 1  | 1.2.3.4       |
      | 2  | 5.6.7.8/32    |
      | 3  | 22.22.22.0/24 |

    Examples: v6 IPs
      | PK | IP            |
      | 4  | 2000::        |
      | 5  | ::1/128       |
      | 6  | 2000::0/32    |
