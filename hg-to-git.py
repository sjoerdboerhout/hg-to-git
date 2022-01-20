#!/usr/bin/python

import sys
import os
import shutil
import re
import logging
import colorlog
import subprocess
import random
import platform
from datetime import datetime
from optparse import OptionParser
from pathlib import Path

# Init global variables
# ----------------------------------------------------------------------------------------------------------------------

# Save current working directory as root for all relative paths
CWD = os.getcwd()

# Global logger
LOGGER = None

LINE_WIDTH = 100


# Function definitions
# ----------------------------------------------------------------------------------------------------------------------

# Parse command line agument to options
def parse_options():

    parser = OptionParser()

    parser.add_option("-a", "--authors", 
                        dest="authorsmap", 
                        default="authors.map",
                        help="Author.map file to use during conversion"
                     )

    parser.add_option("-b", "--bash", 
                        dest="bash", 
                        default="C:\\Program Files\\Git\\bin\\bash.exe",
                        help="Reference to bash (for git)"
                     )

    parser.add_option("-c", "--checks", 
                        dest="checks", 
                        default=False,
                        help="Enable HG repo checks before migration"
                     )

    parser.add_option("-d", "--debug",
                        action="store_true", 
                        dest="debug", 
                        default=False,
                        help="Enable debug logging"
                     )

    parser.add_option("-f", "--force",
                        action="store_true", 
                        dest="force", 
                        default=False,
                        help="Do not halt conversion on validation warnings or errors"
                     )

    parser.add_option("-s", "--source", 
                        dest="source",
                        default="source",
                        help="Source repository containing the Hg repositories"
                     )

    parser.add_option("-t", "--target", 
                        dest="target",
                        default="target",
                        help="Target directory for Git repositories"
                     )

    parser.add_option("-u", "--user", 
                        dest="username",
                        default=f"{os.getenv('USERNAME')}",
                        help="User who runs this script"
                     )

    parser.add_option("-v", "--verbose",
                        action="store_true", 
                        dest="verbose", 
                        default=False,
                        help="Enable verbose logging"
                     )

    (options, args) = parser.parse_args()

    # Convert to absolute path if a relative path was given
    options.source      = os.path.abspath(options.source)
    options.target      = os.path.abspath(options.target)
    options.authorsmap  = os.path.abspath(options.authorsmap)

    return options


# Print iterations progress
def print_progressbar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 82, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if len(prefix) < 1:
        prefix = "                 "
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


# Ask a Yes-No question and handle the user input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


# Create and initialize the logger of this script
def create_logger(log_dir='log', log_file=None, logger_name='appLogger', log_level=logging.INFO):
    """Log plain text to file and to terminal with colors"""

    if log_file == None:
        curr_dateTime = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        log_file = f'{curr_dateTime}_app.log'

    logger = logging.getLogger(logger_name)


    # Log to file (but not to terminal)
    if log_dir == None:
        log_file_path = log_file
    elif not os.path.isdir(log_dir):
        os.mkdir(log_dir)
        log_file_path = os.path.join(log_dir, log_file)
    else:
        log_file_path = os.path.join(log_dir, log_file)

    logfile_handler = logging.FileHandler(log_file_path)
    plain_formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s | %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
        )
    logfile_handler.setFormatter(plain_formatter)  


    # Logging info level to stdout with colors
    terminal_handler = colorlog.StreamHandler()
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(log_color)s%(levelname)-8s | %(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        secondary_log_colors={},
        style='%'
    )
    terminal_handler.setFormatter(color_formatter)

    logger.setLevel(log_level)

    # Add handlers to logger
    logger.addHandler(logfile_handler)
    logger.addHandler(terminal_handler)
    
    return logger


# Find all Hg repositories in the given root directory and it's subdirectories
def get_hg_repos(hg_root_dir):
    reg_compile = re.compile(".hg")
    result = []

    for root, subdirectories, files in os.walk(hg_root_dir):
       for subdirectory in subdirectories:
            print_progressbar(random.randint(0,99), 100)
            if(reg_compile.match(subdirectory)):
                result.append(os.path.relpath(root, hg_root_dir))    
    
    print_progressbar(100, 100)
       
    return result


# Create Author map from given list of repositories
def create_authormap(source_dir=None, hg_repos=[], authorsmap=None):
    authors = set()
    idx = 0
    hg_repo_list_count = len(hg_repos)

    for repo in hg_repos:
        LOGGER.debug(f"- {str(repo).ljust(LINE_WIDTH)}")
        idx += 1
        print_progressbar(idx, hg_repo_list_count)
        cmd = ['hg', 'log', '--template', '{author}\n']
        output = subprocess.check_output(cmd, cwd=os.path.join(source_dir, repo)).decode('utf8')
        authors = authors.union(output.splitlines())
        authors = authors.union(output.splitlines())

    authors = sorted(authors, key=str.casefold)
    if LOGGER.debug:
        LOGGER.debug(f"Found {len(authors)} unique authors in the Mercurial repositories")
        for author in authors:
            LOGGER.debug(f"- {author}")

    authors_map = os.path.join(CWD, authorsmap)

    with open(authors_map, 'wb') as f:
        for author in authors:
            if '@' in author and ' <' in author:
                # Already a valid git author:
                git_author = author
            elif '@' in author:
                # Need to prepend a username, use the email prefix:
                git_author = author.strip('<>').split('@', 1)[0] + ' <' + author + '>'
            else:
                # Need to append an email address, use johndoe@besi.com:
                git_author = author + ' <johndoe@besi.com>'
            f.write(u'"{}"="{}"\n'.format(author, git_author).encode('utf-8'))        


# Validate existing Mercurial repositories
def validate_hg_repos(source_dir=None, hg_repos=[]):
    hg_repos_with_issues = list()
    idx = 0
    hg_repos_count = len(hg_repos)

    LOGGER.info("- Verify branch names (hg branches --closed --template) ---------------------------------")
    for repo in hg_repos:
        idx += 1
        print_progressbar(idx, hg_repos_count)
        cmd = ['hg', 'branches', '--closed', '--template', '{branch}\n']
        output = subprocess.check_output(cmd, cwd=os.path.join(source_dir, repo)).decode('utf8')
        branches = output.splitlines()
        lower = [b.lower() for b in branches]
        problematic = [b for b in branches if lower.count(b.lower()) > 1]
        if problematic:
            #LOGGER.warning("")
            LOGGER.warning(f"Problematic branch names in {repo}:")
            for name in sorted(problematic):
                LOGGER.warning(f"- {str(name).ljust(LINE_WIDTH)}")
                LOGGER.warning("-----------------------------------------------------------------------------------------")
                hg_repos_with_issues.append(repo)

    # Find branches with multiple heads. Something git can't handle
    LOGGER.info("- Check for multiple heads (hg heads -c | grep branch: | sort | uniq -c -d) -------------")
    idx = 0
    for repo in hg_repos:
        idx += 1
        print_progressbar(idx, hg_repos_count)
        repo_dir = os.path.join(source_dir, repo)

        ps1 = subprocess.Popen(('hg', 'heads', '-c')         , cwd=repo_dir                  , stdout=subprocess.PIPE)
        ps2 = subprocess.Popen(('grep', 'branch:')           , cwd=repo_dir, stdin=ps1.stdout, stdout=subprocess.PIPE)
        ps3 = subprocess.Popen(('sort')                      , cwd=repo_dir, stdin=ps2.stdout, stdout=subprocess.PIPE)
        output = subprocess.check_output(('uniq', '-c', '-d'), cwd=repo_dir, stdin=ps3.stdout).decode('utf8')
        ps1.wait()
        ps2.wait()
        ps3.wait()
        branches = output.splitlines()

        lower = [b.lower() for b in branches]
        problematic = [b for b in branches if lower.count(b.lower()) > 0]
        if problematic:
            LOGGER.warning(f"Multiple heads found in '{repo}' in branche(s):                                         ")
            for name in sorted(problematic):
                LOGGER.warning(f"- {str(name).ljust(LINE_WIDTH)}")
                branch = name.split(":")[-1].strip()
                ps1 = subprocess.Popen(('hg', 'heads', branch, '-c'), cwd=os.path.join(source_dir, repo), stdout=subprocess.PIPE)
                output = subprocess.check_output(('grep', 'changeset:'), stdin=ps1.stdout, cwd=os.path.join(source_dir, repo)).decode('utf8')
                ps1.wait()
                revisions = output.strip().split("\n")
                for rev in revisions:
                    LOGGER.warning(f"     rev:   {rev.split(':')[-2]}\t({rev.split(':')[-1]})")
                LOGGER.warning("")

            LOGGER.warning("-----------------------------------------------------------------------------------------")
            hg_repos_with_issues.append(repo)

    hg_repos_with_issues.sort()

    return hg_repos_with_issues


# Init empty git repositories
def init_git_repositories(target_dir="target", hg_repos=[]):
    idx = 0
    hg_repo_list_count = len(hg_repos)

    # Just remove any existing conversions
    #os.removedirs(target_dir)
    shutil.rmtree(target_dir, ignore_errors=True)

    for repo in hg_repos:
        git_repo_path = os.path.join(target_dir, repo)
        LOGGER.debug(f"- {str(git_repo_path).ljust(LINE_WIDTH)}")
        idx += 1
        print_progressbar(idx, hg_repo_list_count)

        os.makedirs(git_repo_path)
               
        cmd = ['git', 'init']
        output = subprocess.check_output(cmd, cwd=git_repo_path).decode('utf8')
        
        cmd = ['git', 'config', 'core.ignoreCase', 'false']
        output = subprocess.check_output(cmd, cwd=git_repo_path).decode('utf8')
        

# Convert all Hg repositories to Git with the fast_export script
def convert_hg_to_git_repository(target_dir="target", hg_repos=[]):
    idx = 0
    hg_repo_list_count = len(hg_repos)

    LOGGER.info(f"Convert each Hg repository to a Git repository with 'fast-export'")
    for repo in hg_repos:
        git_repo_path = os.path.join(CWD, target_dir, repo)
        LOGGER.debug(f"- {str(git_repo_path).ljust(LINE_WIDTH)}")
        idx += 1
        print_progressbar(idx, hg_repo_list_count)

        env = os.environ.copy()
        env['PYTHON'] = sys.executable
        env['PATH'] = os.path.join(CWD, 'fast-export') + os.pathsep + env.get('PATH', '')
        env['HGENCODING'] = 'UTF-8'
        hgFastExportPath = 'hg-fast-export.sh'
        hgRepoPath = os.path.join(options.source, repo)

        operatingsystem = platform.system()
        if (operatingsystem == "Linux"):
            bash = '/bin/bash'
        elif (operatingsystem == "Darwin"):
            bash = '/bin/bash'
        elif (operatingsystem == "Windows"):
            bash=options.bash
            
        cmd = [bash, hgFastExportPath, '-r', hgRepoPath, '-A', options.authorsmap]

        LOGGER.info(f"- Migrate repo '{hgRepoPath}' to Git '{git_repo_path}'")
        try:
            output = subprocess.check_output(
                cmd, 
                cwd=git_repo_path,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env
            )
        except subprocess.CalledProcessError as exc:
            LOGGER.error("Status : FAIL", exc.returncode, exc.output)
            sys.exit(2)
        else:
            if options.verbose:
                LOGGER.debug("Output: \n{}\n".format(output))
            LOGGER.info(f"Finished work on repo '{repo}'")


# Main function of the script controlling the flow
def main(options):

    LOGGER.info("----------------------------==========  Hg to Git  ==========----------------------------")
    LOGGER.info(f"Date Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    LOGGER.info(f"User name      : {options.username}")
    LOGGER.info(f"Current dir    : {CWD}")
    LOGGER.info(f"Source dir     : {options.source}")
    LOGGER.info(f"Target dir     : {options.target}")
    LOGGER.info(f"Authormap      : {options.authorsmap}")
    LOGGER.info(f"Check hg repos : {options.checks}")
    LOGGER.info(f"Halt on error  : {not options.force}")
    LOGGER.info(f"Debug mode     : {options.debug}")
    LOGGER.info(f"Verbose mode   : {options.verbose}")
    LOGGER.info("-----------------------------------------------------------------------------------------")

    if options.source is None or not os.path.isdir(options.source):
        LOGGER.critical(f"Given source dir '{options.source}' doesn't exist or is not a directory...")
        sys.exit(0)

    if options.target is None or not os.path.isdir(options.target):
        LOGGER.critical(f"Given target dir '{options.target}' doesn't exist or is not a directory...")
        sys.exit(0)

    LOGGER.info("")
    LOGGER.info("- Get a list of all Hg repositories -----------------------------------------------------")

    hg_repos = get_hg_repos(options.source)

    LOGGER.info(f"Found {len(hg_repos)} repositories")
    if options.verbose:
        for hg_repo in hg_repos:
                    LOGGER.info(f"  - {hg_repo}")

    LOGGER.info("")

    if not os.path.exists(options.authorsmap):
        LOGGER.error(
            f"{options.authorsmap} not found..."
        )
        LOGGER.info("- Create Author Map ---------------------------------------------------------------------")
        create_authormap(options.source, hg_repos, options.authorsmap)
        LOGGER.info("-----------------------------------------------------------------------------------------")
        LOGGER.error(
            f"Created 'authors.map' from given Hg repositories for you.{os.linesep}" \
            f"                  | Please verify the content of the file and run this script again with equal arguments."
        )
        sys.exit(0)

    LOGGER.info("")
    LOGGER.info("- Verify all Hg repositories for possible issues ----------------------------------------")

    if options.checks:
        hg_repos_with_issues = validate_hg_repos(options.source, hg_repos)
        if len(hg_repos_with_issues) > 0 and not options.force:
            LOGGER.error(f"Found {len(hg_repos_with_issues)} Mercurial repositories with issues that will result in a failing migration {os.linesep}" \
                        f"                  | to git. Please fix them manually by (dummy) merging the heads and retry running this {os.linesep}" \
                        f"                  | script with the same arguments. ")
            if query_yes_no("                  | Do you want to fix this first?", "yes"):
                LOGGER.info(f"Possible fix for multiple heads with only one open head is a dummy merge:")
                LOGGER.info(f"  hg update -C tip # jump to one head")
                LOGGER.info(f"  hg merge otherhead # merge in the other head")
                LOGGER.info(f"  hg revert -a -r tip # undo all the changes from the merge")
                LOGGER.info(f"  hg commit -m 'eliminate other head' # create new tip identical to the old")
                LOGGER.info(f"  OR")
                LOGGER.info(f"  Strip the parts that you don't want to convert from the repository")
                LOGGER.info(f"  OR")
                LOGGER.info(f"  Clone the current repostory with only the branches you want to have in Git")
                LOGGER.info(f"Summary of repositories to check: (All details can be found in the log file './log/') ")
                for repo in hg_repos_with_issues:
                    LOGGER.info(f"- {os.path.join(options.source, repo)}")
                sys.exit(0)
    else:
        LOGGER.info("Checking HG repositories skipped as requested by user '{options.username}'")

    LOGGER.info("")
    LOGGER.info("- Init a Git repositories for each Hg repository ----------------------------------------")
    init_git_repositories(options.target , hg_repos)

    LOGGER.info("")
    LOGGER.info("- Start migration from hg to git --------------------------------------------------------")
    convert_hg_to_git_repository(options.target, hg_repos)

# -------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    options = parse_options()

    if options.debug:
        LOGGER = create_logger(log_level=logging.DEBUG)
    else:
        LOGGER = create_logger()

    main(options)