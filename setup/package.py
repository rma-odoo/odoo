#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import optparse
import os
import pexpect
# import shutil
import time
from contextlib import contextmanager
from glob import glob
from os.path import join
from subprocess import check_output


#----------------------------------------------------------
# Utils
#----------------------------------------------------------
def mkdir(d):
    if not os.path.isdir(d):
        os.makedirs(d)

def system(l, chdir=None):
    print l
    if chdir:
        cwd = os.getcwd()
        os.chdir(chdir)
    if isinstance(l, list):
        rc = os.spawnvp(os.P_WAIT, l[0], l)
    elif isinstance(l, str):
        tmp = ['sh', '-c', l]
        rc = os.spawnvp(os.P_WAIT, tmp[0], tmp)
    if chdir:
        os.chdir(cwd)
    return rc

class OdooDocker(object):
    def __init__(self):
        self.log_file = open('/tmp/logfile.log', 'w')  # FIXME sle: create temporary file
        self.port = 8069  # FIXME sle: get free port
        self.prompt_re = '(\r\nroot@|bash-).*# '
        self.timeout = 600

    def system(self, command):
        self.docker.sendline(command)
        self.docker.expect(self.prompt_re)

    def start(self, docker_image, build_dir):
        self.docker = pexpect.spawn(
            'docker run -v %s:/opt/release -p 127.0.0.1:%s:8069'
            ' -t -i %s /bin/bash --noediting' % (build_dir, self.port, docker_image),
            timeout=self.timeout
        )
        time.sleep(2)  # let the bash start
        self.docker.logfile_read = self.log_file
        self.id = check_output('docker ps -l -q', shell=True)

    def end(self):
        self.docker.close()
        system('docker rm -f %s' % self.id)

@contextmanager
def docker(docker_image, build_dir):
    _docker = OdooDocker()
    try:
        _docker.start(docker_image, build_dir)
        try:
            yield _docker
        except Exception, e:
            print(e)
            # TODO sle: save the log
    finally:
        _docker.end()

#----------------------------------------------------------
# Stages
#----------------------------------------------------------
def _prepare_build_dir(o):
    """The first step of the building process is to prepare the build folder. This processing
    includes an rsync of the current odoo_dir into build_dir and a move of all the addons under an
    unique directory.
    """
    cmd = ['rsync', '-a', '--exclude', '.git', '--exclude', '*.pyc', '--exclude', '*.pyo']
    system(cmd + ['%s/' % o.odoo_dir, o.build_dir])
    # for i in glob.glob(join(o.build_dir, 'addons/*')):
    #     shutil.move(i, join(o.build_dir, 'openerp/addons'))

def build_tgz(o):
    """.tgz build process"""
    system(['python2', 'setup.py', '--quiet', 'sdist'], o.build_dir)
    system(['cp', glob('%s/dist/openerp-*.tar.gz' % o.build_dir)[0], '%s/odoo.tar.gz' % o.build_dir])

def build_deb(o):
    """.deb build process"""
    system(['dpkg-buildpackage', '-rfakeroot', '-uc', '-us'], o.build_dir)
    system(['cp', glob('%s../openerp_*.deb' % o.build_dir)[0], '%s/odoo.deb' % o.build_dir])

def build_rpm(o):
    """.rpm build process"""
    system(['python2', 'setup.py', '--quiet', 'bdist_rpm'], o.build_dir)
    system(['cp', glob('%s/dist/openerp-*.noarch.rpm' % o.build_dir)[0], '%s/odoo.rpm' % o.build_dir])

#----------------------------------------------------------
# Docker testing
#----------------------------------------------------------
def test_tgz(o):
    with docker('debian:stable', o.build_dir) as wheezy:
        wheezy.system('apt-get update -qq && apt-get upgrade -qq -y')
        wheezy.system("apt-get install postgresql python-dev postgresql-server-dev-all python-pip build-essential libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libssl-dev libjpeg-dev -y")
        wheezy.system("service postgresql start")
        wheezy.system('su postgres -s /bin/bash -c "pg_dropcluster --stop 9.1 main"')
        wheezy.system('su postgres -s /bin/bash -c "pg_createcluster --start -e UTF-8 9.1 main"')
        wheezy.system('pip install -r /opt/release/requirements.txt')
        wheezy.system('/usr/local/bin/pip install /opt/release/odoo.tar.gz')
        wheezy.system("useradd --system --no-create-home openerp")
        wheezy.system('su postgres -s /bin/bash -c "createuser -s openerp"')
        wheezy.system('su postgres -s /bin/bash -c "createdb mycompany"')
        wheezy.system('mkdir /var/lib/openerp')
        wheezy.system('chown openerp:openerp /var/lib/openerp')
        wheezy.system('su openerp -s /bin/bash -c "odoo.py --addons-path=/usr/local/lib/python2.7/dist-packages/openerp/addons,/usr/local/lib/python2.7/dist-packages/openerp-addons -d mycompany -i base"')

def test_deb(o):
    with docker('debian:stable', o.build_dir) as wheezy:
        # apt-get will output the prompt and mess up the expect so force it to be quiet
        wheezy.system('/usr/bin/apt-get update -qq && /usr/bin/apt-get upgrade -qq -y')
        wheezy.system('/usr/bin/dpkg -i /opt/release/odoo.deb')
        wheezy.system('/usr/bin/apt-get install -f -y')
        wheezy.system('service openerp start')

def test_rpm(o):
    with docker('centos:centos7', o.build_dir) as centos7:
        centos7.system('rpm -Uvh http://dl.fedoraproject.org/pub/epel/beta/7/x86_64/epel-release-7-0.2.noarch.rpm')
        centos7.system('yum update -y && yum upgrade -y')
        centos7.system('yum install python-pip gcc python-devel -y')
        centos7.system('pip install pydot pyPdf vatnumber xlwt http://download.gna.org/pychart/PyChart-1.39.tar.gz')
        centos7.system('yum install /opt/release/odoo.rpm -y')
        # Systemd doesn't run inside docker
        centos7.system('su openerp -s /bin/bash -c "openerp-server -c /etc/openerp/openerp-server.conf"')

#----------------------------------------------------------
# Options and Main
#----------------------------------------------------------
def options():
    op = optparse.OptionParser()
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    build_dir = "%s-%s" % (root, timestamp)

    op.add_option("-b", "--build-dir", default=build_dir, help="build directory (%default)", metavar="DIR")
    op.add_option("-p", "--pub", default=None, help="pub directory (%default)", metavar="DIR")
    op.add_option("-v", "--version", default='8.0', help="version (%default)")
    op.add_option("", "--no-testing", action="store_true", help="don't test the builded packages")

    op.add_option("", "--no-debian", action="store_true", help="don't build the debian package")
    op.add_option("", "--no-rpm", action="store_true", help="don't build the rpm package")
    op.add_option("", "--no-tarball", action="store_true", help="don't build the tarball")

    (o, args) = op.parse_args()
    # derive other options
    o.odoo_dir = root
    o.timestamp = timestamp
    o.version_full = '%s-%s' % (o.version, o.timestamp)
    return o


def main():
    o = options()
    _prepare_build_dir(o)

    try:
        if not o.no_tarball:
            build_tgz(o)
            if not o.no_testing:
                test_tgz(o)

        if not o.no_debian:
            build_deb(o)
            if not o.no_testing:
                test_deb(o)

        if not o.no_rpm:
            build_rpm(o)
            if not o.no_testing:
                test_rpm(o)
    except:
        raise
    finally:
        if not o.no_testing:
            system("docker rm -f `docker ps -a | grep Exited | awk '{print $1 }'` 2>>/dev/null")


if __name__ == '__main__':
    main()
