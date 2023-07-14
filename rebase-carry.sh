#!/usr/bin/bash
#
# Helper script for OpenShift downstream rebases. Details of the process:
# https://github.com/openshift/kubernetes/blob/master/REBASE.openshift.md
#
# Creates a tsv file with list of carry patches for the current repository.
# Filename needs to be given as a parameter

if [[ $# -ne 1 ]]; then
	echo "Error: Exactly one parameter required: name of the file to be created."
	exit 1
fi

tsvfile=$1

# Version tag: the latest one in the current branch or whatever is in the
# VERSION env variable
version=${VERSION:-$(git tag -l --sort=v:refname | tail -1)}

if [[ -z $version ]]; then
	echo "Error: Failed to determine the version tag"
	exit 2
fi

# Determine repo URLs from remote names: defaults
# are "openshift" for downstream, "upstream" for upstream
# can be overriden by UPSTREAM / DOWNSTREAM env variables
ocp_url=${DOWNSTREAM:-$(git remote get-url openshift)}
upstream_url=${UPSTREAM:-$(git remote get-url upstream)}

# Turn ssh URL to https
ocp_url=${ocp_url/#git@github.com:/https:\/\/github.com\/}
ocp_url=${ocp_url%.git}
upstream_url=${upstream_url/#git@github.com:/https:\/\/github.com\/}
upstream_url=${upstream_url%.git}

if [[ -z $ocp_url ]]; then
	echo "Error: Could not determine the downstream repository URL."
	exit 3
fi
if [[ -z $upstream_url ]]; then
	echo "Error: Could not determine the upstream repository URL."
	exit 4
fi

if [[ -f $tsvfile ]]; then
	read -p "The file $tsvfile already exists. Overwrite? [y/n]: " overwrite
	if [[ "$overwrite" != "y" && "$overwrite" != "Y" ]]; then
		exit 5
	fi
fi

echo
echo "Upstream repo:   $upstream_url"
echo "Downstream repo: $ocp_url"
echo "Version tag:     $version"
echo
echo -e 'Comment Sha\tAction\tClean\tSummary\tCommit link\tPR link' > $tsvfile
git log $( git merge-base openshift/master $version )..openshift/master --ancestry-path --reverse --no-merges --pretty="tformat:%h%x09%x09%x09%s%x09$ocp_url/commit/%h?w=1" \
	| grep -E $'\t''UPSTREAM: .*'$'\t' | sed -E "s~UPSTREAM: ([0-9]+)(:.*)~UPSTREAM: \1\2\t$upstream_url/pull/\1~" >> $tsvfile

echo "Results written in $tsvfile"
