# ###################################################################################
# Business Source License 1.1

# This file is licensed under the Business Source License 1.1 (BSL 1.1). 
# You may not use this file except in compliance with the License.

# You may obtain a copy of the License at:
# https://mariadb.com/bsl11

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# Change Date: 2028-08-01 (3 years from initial release)

# On the Change Date, the License will change to a specified open source license:
# Apache License, Version 2.0

# Original Developer: CoreOps.AI 
# Original License Date: 2025-07-24
# ###################################################################################

from setuptools import setup, find_packages
from pathlib import Path

# Read dependencies from 'requierments.txt'
def parse_requirements():
    requirements_file = Path(__file__).parent / "requirements.txt"
    with open(requirements_file) as f:
        return f.read().splitlines()

setup(
    name='agentcore',
    version='0.5.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'agentcore=agentcore.cli.main:cli',
            'ag=agentcore.cli.main:cli'
        ],
    },
    install_requires=parse_requirements(),
    author='Coreops.AI',
    author_email='support-agentcore@coreops.ai',
    description='Artificial Intelligence Platform',
    url='https://github.com/CoreOps-AI/agentcore-cli',
    project_urls={
        "Repository": "https://github.com/CoreOps-AI/agentcore-cli",
    },
)
