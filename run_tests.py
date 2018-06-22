#!/usr/bin/env python3

# Copyright 2017-2018 Jussi Pakkanen et al
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

import os, subprocess
import createmsi

def build_binaries():
    msvcrt_file = 'msvcrt/program.cpp'
    msvcrt_staging_dir = 'msvcrt/main'
    msvcrt_binary_out = 'msvcrt/main/program.exe'
    if not os.path.exists(msvcrt_staging_dir):
        os.mkdir(msvcrt_staging_dir)
    subprocess.check_call(['cl', '/O2', '/MD', '/EHsc', msvcrt_file, '/Fe' + msvcrt_binary_out])
    os.unlink('program.obj')

if __name__ == '__main__':
    testdirs = [('basictest', 'msidef.json'),
                ('two_items', 'two.json'),
                ('msvcrt', 'msvcrt.json'),
                ('icons', 'icons.json'),
    ]

    build_binaries()
    for d in testdirs:
        os.chdir(d[0])
        createmsi.run([d[1]])
        os.chdir('..')
