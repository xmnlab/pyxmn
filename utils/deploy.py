# -*- coding: utf-8 -*-
"""
Prepares the stage to run the software

"""
import os

# internal modules
from pyxmn.db import conn as db


def prepare_db(settings, stage='local', verbose=False):
    """
    Prepare the stage to run the software

    @return: boolean

    """
    db.Pool.connect()
    cur = db.Pool.cursor()

    # executes the create table script
    db.Pool.execute(
        cur, open(settings.path('db') + 'create.sql').read(), ()
    )

    # executes the prepare script
    db.Pool.execute(
        cur, open(settings.path('db') + 'prepare.sql').read(), ()
    )

    db.Pool.commit()
    cur.close()

    if verbose:
        print('prepare db: OK')

    return True


def pep8(settings):
    """
    Execute pep8 command to check the files project

    @return: Success
    @rtype: boolean

    """
    # Don't execute test function when the hostname not in hosts_dev list
    if settings.HOSTNAME not in settings.HOSTS_DEV:
        return False
    print('pep8 - checking ...')
    # execute pep8 command
    out = os.popen('pep8 %s' % settings.path('root')).read()
    # print pep8 output
    print(out)
    # assert if don't have any pep8 error
    assert(out == '')

    print('pep8 - ok\n')
    # Success
    return True


def doc(settings, just_test=True):
    """
    Execute epydoc function

    """
    # Don't execute test function when the hostname not in hosts_dev list
    if settings.HOSTNAME not in settings.HOSTS_DEV:
        return False

    print('epydoc - checking ...')
    # execute epydoc command
    path = settings.path('root')
    # check if it is a test or it will generate doc files into project
    if just_test:
        path_temp = settings.path('temp')
        cmd = ("epydoc --html -v -o %sepydoc %s" % (path_temp, path))
    else:
        # clear old files
        path_doc = path + 'doc/'
        files = filter(os.path.isfile, os.listdir(path_doc))
        for f in files:
            os.remove(f)
        # generate doc files
        cmd = ("epydoc --html -v -o %s %s" % (path_doc, path))

    out = os.popen(cmd).read()
    # print epydoc output
    print(out)
    # assert if don't have any epydoc error
    assert(len(out.splitlines()) == 1)

    print('epydoc - ok\n')
    # Success
    return True


def test(settings):
    """
    Test pep8 structure and the tests classes

    @return: Success
    @rtype: boolean

    """
    # Don't execute test function when the hostname not in hosts_dev list
    if settings.HOSTNAME not in settings.HOSTS_DEV:
        return False

    # execute pep8 command
    pep8()
    # execute epydoc command
    doc()
    print('test - checking ...')
    # execute test command
    path = '/'.join(settings.path('root').split('/')[:-2])
    cmd = ("cd %s; python -m unittest discover -v ." % path)
    out = os.popen(cmd).read()
    # print test output
    print(out)
