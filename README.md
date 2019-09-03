# timesheets.py

Manage PLATO timesheets

## Usage

```
usage: timesheets.py COMMAND [<args>]

commands:
   submit     Submit any available personal timesheets
   approve    Approve all overdue timesheets for direct reports

Submit and approve PLATO timesheets.

positional arguments:
  COMMAND        Subcommand to run

optional arguments:
  -h, --help     show this help message and exit
  -u USERNAME    Use the supplied value for the NetID authentication
  -p PASSWORD    Use the supplied value for the password
  -v, --verbose  Output extra info (more -v's = more info)
  -t, --test     Run in test mode (no changes are made)
  ```

  ## Requirements

  - Python 3 (`>=3.6`)
  - [WebDriver library](https://github.com/amikeal/web-driver)