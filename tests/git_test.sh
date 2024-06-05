#!/bin/bash

## Returns "*" if the current git branch is dirty.
function evil_git_dirty {
  [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "No" ]] && echo "Yes"
}

## Returns the number of untracked files.
function evil_git_num_untracked_files {
  expr `git status --porcelain 2>/dev/null| grep "^??" | wc -l` 
}

## Get number of files added to the index (but uncommitted)
function evil_git_num_uncommitted_staged_files {
  expr $(git status --porcelain 2>/dev/null| grep "^M" | wc -l)
}

## Get number of files that are uncommitted and not added
function evil_git_num_uncommitted_unstaged_files {
  expr $(git status --porcelain 2>/dev/null| grep "^ M" | wc -l)
}

## Get number of total uncommitted files
function evil_git_num_total_uncommitted_files {
  expr $(git status --porcelain 2>/dev/null| egrep "^(M| M)" | wc -l)
}

## Note: The 2>/dev/null filters out the error messages so you can use 
## these commands on non-git directories. (They'll simply return 0 for the file counts.)

# echo -e "\n[ evil_git_dirty ]: "
printf "\nIs current git branch dirty:\t"
evil_git_dirty
echo "$?"

# echo -e "\n[ evil_git_num_untracked_files ]: "
printf "\n# untracked files:\t\t"
evil_git_num_untracked_files
echo "$?"


# echo -e "\n[ evil_git_num_uncommitted_staged_files ]: "
printf "\n# added but uncommitted files:\t"
evil_git_num_uncommitted_staged_files
echo "$?"


# echo -e "\n[ evil_git_num_uncommitted_unstaged_files ]: "
printf "\n# unstaged & uncommitted files:\t"
evil_git_num_uncommitted_unstaged_files
echo "$?"

# echo -e "\n[ evil_git_num_total_uncommitted_files ]: "
printf "\nTotal # uncommitted files:\t"
evil_git_num_total_uncommitted_files
echo "$?"

printf "\n"
