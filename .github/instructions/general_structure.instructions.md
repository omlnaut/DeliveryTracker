---
applyTo: '**'
---
# Purpose of this repository
This repository contains a collection of azure functions that handle certain automations.
These are mostly timer-based functions (usecases) that run at specific intervals to perform tasks such as checking for certain emails or checking for updates in manga series.
Additionally, some functions are triggered via eventGrid (infrastructure). These functions are used to react if the usecase functions found an update. Examples are creating a new task in google calendar or sending a message via telegram.
To achieve this, the repository uses Azure Functions with a Python runtime.

# General Structure
Base path for the repository (inside its devcontainer) is `/workspaces/DeliveryTracker/`. The underlying folders that you need to know about are:
- `infrastructure`: Contains functions that are usually triggered by eventGrid. They react to changes made by the usecase functions.
- `usecases`: Contains functions that are usually triggered by a timer. They perform the actual tasks, such as checking for new emails or updates in manga series.
- `shared`: Contains shared code that is used by multiple usecases or infrastructure functions. This includes:
    - clients for interacting with google services, reddit, etc.
    - utility functions for interacting with the azure hosting environment
    - general utility functions like date comparisons
- `function_app.py`: The main entry point for the Azure Functions app. It is responsible for loading the functions from the `usecases` and `infrastructure` folders and registering them with the Azure Functions runtime.

The `investigations` folder is for testing out new use case ideas. The notebooks in there are not guaranteed to work.

# Coding
When creating new python files, the linter will not pick them up automatically. I have to use the "python: restart language server" command in the command palette to make it aware of the new files. This is a limitation of the Azure Functions Python extension.