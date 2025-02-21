# Hanil Zarbailov Devopshift Python Test Repo

This program gets input from the user, uses default values for any invalid input, injects it into a Jinja2 template, creates a Terraform (.tf) file from it, uses the python_terraform package to attempt and apply the configuration.

## Resource Validation
The program validates that the resources got created and it stores the validation data in a .json file (I use mocks if it fails).

## Terraform Destroy
At the end of the program, we ask the user if he wants to destroy the environment that got created (the default is yes) and operate according to the input.

## Logging
The logger is configured with a custom format and the logs are stored in a .log file using a FileHandler and a StreamHandler.
