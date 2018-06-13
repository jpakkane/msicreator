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

import os
import createmsi

if __name__ == '__main__':
    testdirs = [('basictest', 'msidef.json'),
                ('two_items', 'two.json'),
    ]
    for d in testdirs:
        os.chdir(d[0])
        createmsi.run([d[1]])
        os.chdir('..')

