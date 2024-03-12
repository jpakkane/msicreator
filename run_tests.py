#!/usr/bin/env python3

# Copyright 2017-2023 Jussi Pakkanen et al
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys, subprocess, shutil
import createmsi

def build_msvcrt():
    msvcrt_file = 'program.cpp'
    msvcrt_staging_dir = 'msvcrt/main'
    msvcrt_binary_out = 'main/program.exe'
    if not os.path.exists(msvcrt_staging_dir):
        os.mkdir(msvcrt_staging_dir)
    subprocess.check_call(['cl',
                           '/nologo',
                           '/O2',
                           '/MD',
                           '/EHsc',
                           msvcrt_file,
                           '/Fe' + msvcrt_binary_out],
                          cwd='msvcrt')

def build_iconexe():
    staging_dir = 'shortcuts/staging'
    if not os.path.exists(staging_dir):
        os.mkdir(staging_dir)
    subprocess.check_call(['rc', '/nologo', '/fomyres.res', 'myres.rc'],
                          cwd='shortcuts')
    subprocess.check_call(['cl',
                           '/nologo',
                           '/Fprog.obj',
                           '/O2',
                           '/MT',
                           '/c',
                           'prog.c'],
                          cwd='shortcuts')
    subprocess.check_call(['link',
                           '/OUT:staging/iconprog.exe',
                           'myres.res',
                           'prog.obj',
                           '/nologo',
                           '/SUBSYSTEM:WINDOWS',
                           'user32.lib',
                           ],
                          cwd='shortcuts')

def build_guiexe():
    staging_dir = 'customactions/gui'
    if not os.path.exists(staging_dir):
        os.mkdir(staging_dir)
    subprocess.check_call(['cl',
                           '/nologo',
                           '/O2',
                           '/MT',
                           'prog.c',
                           '/link',
                           '/SUBSYSTEM:WINDOWS',
                           '/OUT:gui/gui.exe'
                           ],
                           cwd="customactions")

def build_binaries():
    build_msvcrt()
    build_iconexe()
    build_guiexe()

def install_wix():
    subprocess.check_call(['dotnet',
                           'nuget',
                           'add',
                           'source',
                           'https://api.nuget.org/v3/index.json'])
    subprocess.check_call(['dotnet',
                           'tool',
                           'install',
                           '--global',
                           'wix'])
    subprocess.check_call(['wix',
                           'extension',
                           'add',
                           'WixToolset.UI.wixext',
                           ])

if __name__ == '__main__':
    testdirs = [('basictest', 'msidef.json'),
                ('two_items', 'two.json'),
                ('msvcrt', 'msvcrt.json'),
                ('icons', 'icons.json'),
                ('shortcuts', 'shortcuts.json'),
                ('registryentries', 'registryentry.json'),
                ('majorupgrade', 'majorupgrade.json'),
                ('productguid', 'productguid.json'),
                ('UIgraphics', 'uigraphics.json'),
                #('withoutlicense', 'withoutlicense.json')
                ('customactions', 'customactions.json')
    ]

    if shutil.which('wix') is None:
        install_wix()
    build_binaries()
    for d in testdirs:
        print("\n\nTest:", d[0], '\n')
        os.chdir(d[0])
        createmsi.run([d[1]]) # In case of error this throws a sys.exit.
        os.chdir('..')
    print('All tests pass.')
