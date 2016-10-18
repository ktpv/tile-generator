#!/usr/bin/env python

# tile-generator
#
# Copyright (c) 2015-Present Pivotal Software, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function
import errno
import os
import os.path
import requests
import shutil
import sys
try:
	# Python 3
	from urllib.request import urlretrieve
except ImportError:
	# Python 2
	from urllib import urlretrieve

def download_docker_image(docker_image, target_file, cache=None):
	try:
		from docker.client import Client
		from docker.utils import kwargs_from_env
		kwargs = kwargs_from_env()
		kwargs['tls'] = False
		docker_cli = Client(**kwargs)
		image = docker_cli.get_image(docker_image)
		image_tar = open(target_file,'w')
		image_tar.write(image.data)
		image_tar.close()
	except Exception as e:
		if cache is not None:
			cached_file = os.path.join(cache, docker_image.lower().replace('/','-').replace(':','-') + '.tgz')
			if os.path.isfile(cached_file):
				print('using cached version of', docker_image)
				urlretrieve(cached_file, target_file)
				return
			print(docker_image, 'not found in cache', cache, file=sys.stderr)
			sys.exit(1)
		if isinstance(e, KeyError):
			print('docker not configured on this machine (or environment variables are not properly set)', file=sys.stderr)
		else:
			print(docker_image, 'not found on local machine', file=sys.stderr)
			print('you must either pull the image, or download it and use the --docker-cache option', file=sys.stderr)
		sys.exit(1)


def bosh_extract(output, properties):
	result = {}
	for l in output.split('\n'):
		for p in properties:
			if l.startswith(p['pattern']):
				result[p['label']] = l.split(':', 1)[-1].strip()
	return result

def mkdir_p(dir, clobber=False):
	if os.path.isdir(dir):
		shutil.rmtree(dir)
	try:
		os.makedirs(dir)
		return dir
	except os.error as e:
		if e.errno != errno.EEXIST:
			raise

def download(url, filename, cache=None):
	# [mboldt:20160908] Using urllib.urlretrieve gave an "Access
	# Denied" page when trying to download docker boshrelease.
	# I don't know why. requests.get works. Do what works.
	# urllib.urlretrieve(url, filename)
	if cache is not None:
		basename = os.path.basename(filename)
		cachename = os.path.join(cache, basename)
	 	if os.path.isfile(cachename):
			print('using cached version of', basename)
			shutil.copy(cachename, filename)
			return
	if url.startswith("http:") or url.startswith("https"):
		response = requests.get(url, stream=True)
		response.raise_for_status()
		with open(filename, 'wb') as file:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:
					file.write(chunk)
	else:
		shutil.copy(url, filename)

