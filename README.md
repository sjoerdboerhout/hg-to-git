
# Mercurial to Git converter

This repository contains some scripts to help you converting existing Mercurial repositories to Git repositories.
> **Note:** Some scripts may contain some details or functions specific for the repositories they were originally created for.

# Preparations

## Verify Mercurial and Git are installed
The script assumes that you have both Mercurial and Git already installed on your system

## Install required Python modules
- pip install **mercurial**
- pip install **colorlog**

# Migrate repositories
## Script flow
 1. Read arguments
 2. Verify arguments for valid input
 3. Find all Mercurial repositories in the source directory
 4. Check if authorsmap file is present
	 - If not found the script wil create a new authorsmap based on the found repositories
 5. Validate all Mercurial repositories (optional)
	 - Script will exit if errors are found
 6. Init a new Git repository for each Mercurial repository in the target directory
 7. Convert all Mercurial repositories to Git using the authorsmap file

## Script arguments
- **-a** (*--authors*): Author.map file to use during conversion
  - Default: **authors.map**
- **-b** (*--bash*): Location of bash when running on Windows
  - Default: **C:\Program Files\Git\bin\bash.exe**
- **-c** (*--checks*): Enable HG repository checks before migration
  - Default: **True**
- **-d** (*--debug*): Enable debug logging
  - Default: **False**
- **-f** (*--force*): Do not halt conversion on validation warnings or errors
  - Default: **False**
- **-s** (*--source*): Source repository containing the Hg repositories
  - Default: **./source**
- **-t** (*--target*): Target directory for Git repositories
  - Default: **./source**
- **-u** (*--user*): User who runs this script
  - Default: **Currently logged in user in OS**
- **-v** (*--verbose*): Enable verbose logging
  - Default: **False**
