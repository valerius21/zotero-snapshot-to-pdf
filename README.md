# Zotero Website Snapshot to PDF

This is the complementary repository to [my blog post](https://valerius.me/).

## Disclaimer and development state

Remember to back-up your Zotero Folder. This script is not in a
production-ready state, and has only been in use on MacOS and Linux.

Use it at your own risk!

Currently, it queries only the first 100 sources with snapshots and
uploads duplicates, if the script has been run before.

## Prerequisites

1. Copy over `config.example.toml` to `config.toml` and update it with
   the corresponding data
2. Create a Virtual Environment (optional) and activate it
3. Run `pip install -r requirements.txt`
4. Ensure, Google Chrome is installed and available on the path given
   in the configuration file

## Running the Script

Run `python convert_pdfs.py`

## Drop a citation

If you have used this repository and found it helpful,
I would be delighted, if you would consider a citation.
Thanks!

## To Do

- [ ] use a config parameter to add a caching directory
- [ ] figure out a system specific Chrome resolver
- [ ] ensure chrome is installed on the system
- [ ] install it as a service, re-run on library changes
- [ ] create tmpdir using python libraries
- [ ] skip, if there is already a PDF present
