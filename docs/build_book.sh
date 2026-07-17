#!/usr/bin/env bash
doc_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

### users usually do not need to make changes below this line
### ========================================================================
if [[ "$CONDA_DEFAULT_ENV" != "pyDAmonitor"  ]]; then
  echo -e "\n    !!! source ush/load_pyDAmonitor.sh first !!!\n"
  exit 1
fi
#
# save the origin URL before running ghp-import, which has to use the origin remote
save_origin=$(git remote get-url origin)
#
# kill the whole build process if Ctrl+C is entered but restore the origin remote
cleanup() {
  echo "Caught Ctrl+C. Restoring the origin remote..."
  git remote set-url origin ${save_origin}
  exit 1
}
trap cleanup SIGINT SIGTERM
#
# get the repo url of the book remote
book_repo=$(git remote get-url book)
if [[ -z "${book_repo}" ]]; then
  echo "add a 'book' remote as follows"
  echo "  git remote add book git@github.com:guoqing-noaa/mybook"
  echo "     replace guoqing-noaa/mybook with your own repository"
  exit 1
elif [[ "${book_repo}" ==  *"pyDAmonitor/pyDAmonitor" ]]; then
  echo "ERROR: the 'book' remote tracks the authoritative repository:"
  echo "  ${book_repo}"
  echo "users can ONLY push books to their own repositories."
  exit 1
fi

set -x
### clean the book first and then build
jupyter-book clean ${doc_dir}
jupyter-book build ${doc_dir}

### push book to book_repo
# change origin, ghp-import and then restore origin 
git remote set-url origin ${book_repo}
ghp-import -n -p -f ${doc_dir}/_build/html
git remote set-url origin ${save_origin}

### print out helper information
set +x
account=$(echo "${book_repo}" | awk -F'[:/]' '{print $(NF-1)}')
repo=$(echo "${book_repo}" | awk -F'[:/]' '{print $NF}' | sed 's/\.git$//')
echo -e "\nVisit https://${account}.github.io/${repo} to check the results"
echo " (Github action may take a few minutes to render the updated pages)"
