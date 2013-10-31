#!/usr/bin/python

"""
A script to generate release note entries for BZs of a particular
target milestone. These entries are not necessarily intended to be used as is,
but to serve as a skeleton entry for further enhancement.

Before running this, make sure that you have set your username in
~/.bugzillarc:

[bugzilla.redhat.com]
user = someone@redhat.com

and that you have obtained a Bugzilla session cookie by executing:

$ bugzilla login
"""
import re
from optparse import OptionParser
from sys import exit
from checkbugs import get_bugs

# Super lame.  At least python-bugzilla (and probably the Bugzilla API) does
# not return the name of the bug assignee, just their email.
_email_to_name = {
    'asaha@redhat.com': 'Amit Saha',
    'ncoghlan@redhat.com': 'Nick Coghlan',
    'dcallagh@redhat.com': 'Dan Callaghan',
    'rmancy@redhat.com': 'Raymond Mancy'}

def main():
    parser = OptionParser('usage: %prog [options]',
            description='Generates basic release note entries')
    parser.add_option('-m', '--milestone', metavar='MILESTONE',
        help='Create release note entries for bugs marked against MILESTONE')
    parser.add_option('-f', '--release-note-file',
        help='This is the release note file where the entries will be made')
    options, _ = parser.parse_args()

    if not options.milestone:
        parser.error('Must specify a milestone')
    if not options.release_note_file:
        parser.error('Must specify where the release notes file is')

    # We only care about the milestone
    states = None
    sprint = None
    release = None
    milestone = options.milestone
    bugs = get_bugs(milestone, release, sprint, states)
    if not bugs:
        print 'There are no bugs for milestone %s' % milestone
        return 0
    release_file_path = options.release_note_file
    contents = None
    with open(release_file_path, 'r') as release_file:
        # Release notes are not so big, safe enough to read all at once.
        contents = release_file.read()

    bugs = set(bugs)
    bugs_already_done = set([])
    if contents:
        # Let's build a set of all the issues we can find.
        for bug in bugs:
            if re.search(':issue:`%s`' % bug.id, contents):
                bugs_already_done.add(bug)
    # Get those that we have not found in the release notes already
    bugs_for_entry = bugs_already_done.symmetric_difference(bugs)
    # Let's write them out
    issue_string = ''
    for bug in bugs_for_entry:
        issue_string += '* :issue:`%s`: %s\n  (Contributed by %s)\n' % \
            (bug.id, bug.summary,
                _email_to_name.get(bug.assigned_to, bug.assigned_to))
    if issue_string:
        with open(release_file_path, 'a') as release_file:
            release_file.write(issue_string.encode('utf-8').rstrip())
    return 0

if __name__ in ('main', '__main__'):
    exit(main())
