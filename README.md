# Plaid-with-Multiple-Accounts
This program allows users to calculate and graph summary spend and income for multiple bank accounts using the plaid api. 

An application like this is handy when trying to bridge an individuals total spend/income across multiple bank accounts/credit cards, as looking at the balance and transactions of a single account will not provide the full picture.

## Required
In order to use the application you will need at least 1 bank account and a plaid account. 
Plaid is an api that allows users to connect their banks to applications:https://plaid.com/. The api has 3 account types:
- Sandbox: Testing using a single bank account
- Development: Testing using up to 100 bank accounts
- Production: Unlimited bank accounts (includes a fee)

For this application it is best to have development or production, as the idea is to connect multiple bank account using the api. For information on initial set up and retrieving access tokens, visit the plaid documentation: https://plaid.com/docs/
