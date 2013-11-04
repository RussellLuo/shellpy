#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""List directory contents"""

import sys
import os

ENCODING = sys.getfilesystemencoding() or sys.getdefaultencoding()

def ls(basepath, recursive, list_startswithdot, in_detail, in_detail_numid, one_perline):
    """Main entry of `ls`.
    """
    items = get_items(basepath, recursive, list_startswithdot)
    has_title = recursive or len(items) > 1
    print_items(items, has_title, in_detail, in_detail_numid, one_perline)

def get_items(basepath, recursive, list_startswithdot):
    """Get all items in `basepath`.

    the format of each `item`:
        (
            path,
            (
                (name1, detail1),
                (name2, detail2),
            )
        )
    """
    files, dirs = get_paths(basepath)

    def make_item(path, names):
        upath = unicode(path, ENCODING)
        unames = [unicode(name, ENCODING) for name in names]
        details = [os.stat(os.path.join(upath, uname)) for uname in unames]

        return (upath, tuple(zip(unames, details)))

    def is_target(path):
        # ignore `path` starting with dot (e.g. '.xx') if `list_startswithdot` is not specified
        return list_startswithdot or not os.path.basename(path).startswith(u'.')

    # files will be part of the result items
    items = files and [make_item('', files)]

    # directories need to be processed further
    for path in dirs:
        if recursive: # walk the directory tree
            for dirpath, dirnames, filenames in os.walk(path):
                for i, _ in enumerate(dirnames):
                    if not is_target(dirnames[i]): # don't walk non-target subdirectories
                        del dirnames[i]
                # remove non-target file
                files = filter(is_target, dirnames + filenames)
                items.append(make_item(dirpath, files))
        else:
            # remove non-target file
            files = filter(is_target, os.listdir(path))
            items.append(make_item(path, files))

    return items

def print_items(items, has_title, in_detail, in_detail_numid, one_perline):
    """Print `items` with specified format .
    """
    count = len(items)
    for i, item in enumerate(sort_items(items)):
        path, content = item

        # print title
        if has_title and path:
            print(path + u':')

        # print content
        datas = get_formatted_datas(sort_content(content),
                                    in_detail, in_detail_numid, one_perline)
        print(datas)

        # print a newline if it's not the last item
        if i < count - 1:
            print(u'')

def get_paths(basepath):
    """Get all possible pathnames (files and directories) after expanding `basepath`.
    """
    import glob
    paths = [g for p in basepath for g in glob.glob(p)] # pathname pattern expansion

    files = filter(os.path.isfile, paths) # extract files
    dirs = filter(os.path.isdir, paths) # extract directories
    return (files, dirs)

def get_formatted_datas(content, in_detail, in_detail_numid, one_perline):
    """Get formatted datas from `content`.
    """
    if in_detail_numid or in_detail:
        sep = u'\n'
        datas = []
        for name, detail in content:
            data = u'{}  {}  {}  {}  {:>6}  {}  {}'.format(
                       get_symbol_mode(detail.st_mode),
                       detail.st_nlink,
                       detail.st_uid if in_detail_numid else get_usrname(detail.st_uid),
                       detail.st_gid if in_detail_numid else get_grpname(detail.st_gid),
                       detail.st_size,
                       get_strftime(detail.st_mtime),
                       name)
            datas.append(data)
    else:
        sep = u'\n' if one_perline else u'  '
        datas = [name for name, detail in content]

    return sep.join(datas)

def sort_items(items):
    """Sort `items` by path.
    """
    return sorted(items, key=lambda c: c[0].lower())

def sort_content(content):
    """Sort `content` by name.
    """
    return sorted(content, key=lambda c: c[0].lower())

def get_symbol_mode(mode):
    """Get symbolic mode according to numeric one.
    see http://stackoverflow.com/questions/5337070/how-can-i-get-a-files-permission-mask
    """
    import stat

    def symbol(exp, hit_char):
        return (u'-', hit_char)[bool(exp)]

    def filetype(mode):
        filetype = u'-'
        if stat.S_ISDIR(mode):
            filetype = u'd'
        if stat.S_ISLNK(mode):
            filetype = u'l'
        if stat.S_ISCHR(mode):
            filetype = u'c'
        if stat.S_ISBLK(mode):
            filetype = u'b'
        return filetype

    return (u'{}'*10).format(filetype(mode),
                             symbol(mode & stat.S_IRUSR, u'r'),
                             symbol(mode & stat.S_IWUSR, u'w'),
                             symbol(mode & stat.S_IXUSR, u'x'),
                             symbol(mode & stat.S_IRGRP, u'r'),
                             symbol(mode & stat.S_IWGRP, u'w'),
                             symbol(mode & stat.S_IXGRP, u'x'),
                             symbol(mode & stat.S_IROTH, u'r'),
                             symbol(mode & stat.S_IWOTH, u'w'),
                             symbol(mode & stat.S_IXOTH, u'x'))

def get_usrname(uid):
    """Get user name according to `uid`.
    see http://stackoverflow.com/questions/927866/how-to-get-the-owner-and-group-of-a-folder-with-python-on-a-linux-machine
    """
    import pwd
    return pwd.getpwuid(uid)[0]

def get_grpname(gid):
    """Get group name according to `gid`.
    see http://stackoverflow.com/questions/927866/how-to-get-the-owner-and-group-of-a-folder-with-python-on-a-linux-machine
    """
    import grp
    return grp.getgrgid(gid)[0]

def get_strftime(stat_time):
    """Get a more readable format of `stat_time` (from `os.stat`)
    see http://www.seanelavelle.com/2012/05/04/make-os-stat-times-readable-in-python/
    """
    import time
    seconds = stat_time - time.timezone
    locale_time = time.strftime('%b %d %H:%M', time.gmtime(seconds))
    return unicode(locale_time, ENCODING)

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', nargs='*', default=[os.curdir])
    parser.add_argument('-a', '--all', action='store_true',
                        help='do not ignore entries starting with .')
    parser.add_argument('-l', action='store_true',
                        help='use a long listing format')
    parser.add_argument('-n', '--numeric-uid-gid', action='store_true',
                        help='like -l, but list numeric user and group IDs')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='list subdirectories recursively')
    parser.add_argument('-1', dest='one', action='store_true',
                        help='list one file per line')
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    #print(args)
    ls(args.file, args.recursive, args.all, args.l, args.numeric_uid_gid, args.one)
