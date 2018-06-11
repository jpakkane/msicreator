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

import sys, os, subprocess, shutil, uuid, json
from glob import glob
import platform
import xml.etree.ElementTree as ET

sys.path.append(os.getcwd())

def gen_guid():
    return str(uuid.uuid4()).upper()

class Node:
    def __init__(self, dirs, files):
        assert(isinstance(dirs, list))
        assert(isinstance(files, list))
        self.dirs = dirs
        self.files = files

class PackageGenerator:

    def __init__(self, jsonfile):
        jsondata = json.load(open(jsonfile, 'rb'))
        self.product_name = jsondata['product_name']
        self.manufacturer = jsondata['manufacturer']
        self.version = jsondata['version']
        self.comments = jsondata['comments']
        self.installdir = jsondata['installdir']
        self.license_file = jsondata['license_file']
        self.name = jsondata['name']
        self.guid = '*'
        self.update_guid = jsondata['update_guid']
        self.basename = jsondata['name_base']
        self.main_xml = self.basename + '.wxs'
        self.main_o = self.basename + '.wixobj'
        self.bytesize = 32 if '32' in platform.architecture()[0] else 64
        # rely on the environment variable since python architecture may not be the same as system architecture
        if 'PROGRAMFILES(X86)' in os.environ:
            self.bytesize = 64
        self.final_output = '%s-%s-%d.msi' % (self.basename, self.version, self.bytesize)
        if self.bytesize == 64:
            self.progfile_dir = 'ProgramFiles64Folder'
            redist_glob = 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\VC\\Redist\\MSVC\\*\\MergeModules\\Microsoft_VC141_CRT_x64.msm'
        else:
            self.progfile_dir = 'ProgramFilesFolder'
            redist_glob = 'C:\\Program Files\\Microsoft Visual Studio\\2017\\Community\\VC\\Redist\\MSVC\\*\\MergeModules\\Microsoft_VC141_CRT_x86.msm'
        trials = glob(redist_glob)
        if len(trials) != 1:
            sys.exit('There are more than one potential redist dirs.')
        self.redist_path = trials[0]
        self.component_num = 0
        self.parts = jsondata['parts']
        self.feature_components = {}
        self.feature_components['main'] = []
        tmphack = self.parts[0]
#        for sd in self.staging_dirs:
#            self.feature_components[sd] = []
        self.feature_properties = {'main': {
            'Id': tmphack['id'],
            'Title': tmphack['title'],
            'Description': tmphack['description'],
            'Level': '1'
            }
        }

    def generate_files(self):
        self.root = ET.Element('Wix', {'xmlns': 'http://schemas.microsoft.com/wix/2006/wi'})
        product = ET.SubElement(self.root, 'Product', {
            'Name': self.product_name,
            'Manufacturer': self.manufacturer,
            'Id': self.guid,
            'UpgradeCode': self.update_guid,
            'Language': '1033',
            'Codepage':  '1252',
            'Version': self.version,
        })

        package = ET.SubElement(product, 'Package',  {
            'Id': '*',
            'Keywords': 'Installer',
            'Description': '%s %s installer' % (self.name, self.version),
            'Comments': self.comments,
            'Manufacturer': self.manufacturer,
            'InstallerVersion': '500',
            'Languages': '1033',
            'Compressed': 'yes',
            'SummaryCodepage': '1252',
        })

        if self.bytesize == 64:
            package.set('Platform', 'x64')
        ET.SubElement(product, 'Media', {
            'Id': '1',
            'Cabinet': self.basename + '.cab',
            'EmbedCab': 'yes',
        })
        targetdir = ET.SubElement(product, 'Directory', {
            'Id': 'TARGETDIR',
            'Name': 'SourceDir',
        })
        progfiledir = ET.SubElement(targetdir, 'Directory', {
            'Id': self.progfile_dir,
        })
        installdir = ET.SubElement(progfiledir, 'Directory', {
            'Id': 'INSTALLDIR',
            'Name': self.installdir,
        })
#        ET.SubElement(installdir, 'Merge', {
#            'Id': 'VCRedist',
#            'SourceFile': self.redist_path,
#            'DiskId': '1',
#            'Language': '0',
#        })

        ET.SubElement(product, 'Property', {
            'Id': 'WIXUI_INSTALLDIR',
            'Value': 'INSTALLDIR',
        })
        ET.SubElement(product, 'UIRef', {
            'Id': 'WixUI_FeatureTree',
        })
#        for sd in self.staging_dirs:
#            assert(os.path.isdir(sd))
        feature = self.parts[0]
        top_feature = ET.SubElement(product, 'Feature', {
            'Id': 'Complete',
            'Title': self.name + ' ' + self.version,
            'Description': 'The complete package',
            'Display': 'expand',
            'Level': '1',
            'ConfigurableDirectory': 'INSTALLDIR',
        })
        for sd in [feature['staged_dir']]:
            if '/' in sd or '\\' in sd:
                sys.exit('Staged_dir %s must not have a path segment.' % sd)
            nodes = {}
            for root, dirs, files in os.walk(sd):
                cur_node = Node(dirs, files)
                nodes[root] = cur_node
            self.create_xml(nodes, sd, installdir, sd)
            self.build_features(nodes, top_feature, sd)
#        vcredist_feature = ET.SubElement(top_feature, 'Feature', {
#            'Id': 'VCRedist',
#            'Title': 'Visual C++ runtime',
#            'AllowAdvertise': 'no',
#            'Display': 'hidden',
#            'Level': '1',
#        })
#        ET.SubElement(vcredist_feature, 'MergeRef', {'Id': 'VCRedist'})
        ET.ElementTree(self.root).write(self.main_xml, encoding='utf-8', xml_declaration=True)
        # ElementTree can not do prettyprinting so do it manually
        import xml.dom.minidom
        doc = xml.dom.minidom.parse(self.main_xml)
        with open(self.main_xml, 'w') as of:
            of.write(doc.toprettyxml())

    def build_features(self, nodes, top_feature, staging_dir):
        feature = ET.SubElement(top_feature, 'Feature',  self.feature_properties[staging_dir])
        for component_id in self.feature_components[staging_dir]:
            ET.SubElement(feature, 'ComponentRef', {
                'Id': component_id,
            })

    def create_xml(self, nodes, current_dir, parent_xml_node, staging_dir):
        cur_node = nodes[current_dir]
        if cur_node.files:
            component_id = 'ApplicationFiles%d' % self.component_num
            comp_xml_node = ET.SubElement(parent_xml_node, 'Component', {
                'Id': component_id,
                'Guid': gen_guid(),
            })
            self.feature_components[staging_dir].append(component_id)
            if self.bytesize == 64:
                comp_xml_node.set('Win64', 'yes')
            if self.component_num == 0:
                ET.SubElement(comp_xml_node, 'Environment', {
                    'Id': 'Environment',
                    'Name': 'PATH',
                    'Part': 'last',
                    'System': 'yes',
                    'Action': 'set',
                    'Value': '[INSTALLDIR]',
                })
            self.component_num += 1
            for f in cur_node.files:
                file_id = os.path.join(current_dir, f).replace('\\', '_').replace('#', '_').replace('-', '_')
                ET.SubElement(comp_xml_node, 'File', {
                    'Id': file_id,
                    'Name': f,
                    'Source': os.path.join(current_dir, f),
                })

        for dirname in cur_node.dirs:
            dir_id = os.path.join(current_dir, dirname).replace('\\', '_').replace('/', '_')
            dir_node = ET.SubElement(parent_xml_node, 'Directory', {
                'Id': dir_id,
                'Name': dirname,
            })
            self.create_xml(nodes, os.path.join(current_dir, dirname), dir_node, staging_dir)

    def build_package(self):
        wixdir = 'c:\\Program Files\\Wix Toolset v3.11\\bin'
        if not os.path.isdir(wixdir):
            wixdir = 'c:\\Program Files (x86)\\Wix Toolset v3.11\\bin'
        if not os.path.isdir(wixdir):
            print("ERROR: This script requires WIX")
            sys.exit(1)
        subprocess.check_call([os.path.join(wixdir, 'candle'), self.main_xml])
        subprocess.check_call([os.path.join(wixdir, 'light'),
                               '-ext', 'WixUIExtension',
                               '-cultures:en-us',
                               '-dWixUILicenseRtf=' + self.license_file,
                               '-out', self.final_output,
                               self.main_o])

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(sys.argv[0] + ' <msi definition json>')
    jsonfile = sys.argv[1]
    if '/' in jsonfile or '\\' in jsonfile:
        sys.exit('Input file %s must not contain a path segment.' % jsonfile)
    p = PackageGenerator(jsonfile)
    p.generate_files()
    p.build_package()
