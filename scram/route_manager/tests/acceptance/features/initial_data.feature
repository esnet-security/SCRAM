Feature: Out of the box initial data

    Scenario: As a BHR replacement, it comes with a block actiontype
    When we're logged in
    And  we list the actiontypes

    Then we get a 200 status code
    And the number of actiontypes is 1

    Scenario: Transaction Test Case will truncate the db, losing our initial data;
        retest block actiontype existing
    When we're logged in
    And  we list the actiontypes

    Then we get a 200 status code
    And the number of actiontypes is 1
