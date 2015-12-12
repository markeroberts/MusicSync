import os, posixpath, sys, subprocess

# Settings
MUSIC_DIR = '/home/mark/Music'
PHONE_DIR = '/storage/9016-4EF8/Music'
SYNC_FILETYPES = 'mp3,flac'
ADB_CMD = 'adb'

# Windows only settings
if(os.name == 'nt'):
	MUSIC_DIR = 'D:\Music'
	ADB_CMD = 'adb\\adb'

print('Starting MusicSync v1.0.0-alpha')

# First test ADB connection to device
print('Testing connection to device... ', end='', flush=True)

adbDevices = subprocess.check_output([ADB_CMD, 'devices']).decode().strip()
if(adbDevices.endswith('List of devices attached') or adbDevices.endswith('offline')):
	print('failed! Ensure device is connected and USB debugging is enabled.')
	sys.exit()
	# TODO: check for only one offline device before throwing error
else:
	print('Connected!')

# Build list of local files to sync
print('Scanning local music... ', end='', flush=True)

# If no files found, throw error
if(not os.path.isdir(MUSIC_DIR)):
	print('no files found! Check MUSIC_DIR setting and try again.')
	sys.exit()
else:
	musicFiles = []
	for dirpath, dirnames, filenames in os.walk(MUSIC_DIR):
		for filename in filenames:
			filePath = os.path.join(dirpath, filename)
			if(filePath.split('.')[-1] in SYNC_FILETYPES.split(',')):
				musicFiles.append(filePath[len(MUSIC_DIR):].replace('\\', '/'))

	print('found %d files.' % len(musicFiles))
	# TODO: print list of filetypes found for SYNC_FILETYPES?

# Build list of device files to calculate what needs to be synced
print('Scanning music on device... ', end='', flush=True)

cmdFiles = ADB_CMD + ' shell for file in {0}/* {0}/*/* {0}/*/*/* {0}/*/*/*/*; do echo $file; done'.format(PHONE_DIR)
# TODO: avoid repeating glob, needs to be fully recursive
adb_output = subprocess.check_output(cmdFiles.split(' '))

if(len(adb_output) == 0):
	print('no files found! Check PHONE_DIR setting and try again.')
	sys.exit()
else:
	phoneFiles = [file.strip() for file in adb_output.decode().split(PHONE_DIR)]

	print('found %d files.' % len(phoneFiles))

# Calculate files to sync and display
filesToSync = sorted(list(set(musicFiles) - set(phoneFiles)))
# filesToSync = sorted(list(set(phoneFiles) - set(musicFiles)))

if(len(filesToSync) == 0):
	print('All files are synced!')
else:
	# Display files to sync in a nice way
	print('Files to sync:')

	print(filesToSync[0][1:])
	for i in range(1, len(filesToSync)):
		commonPrefix = os.path.commonprefix([filesToSync[i], filesToSync[i-1]])
		commonPrefix = len(commonPrefix[:commonPrefix.rfind('/') + 1])
		print(' ' * (commonPrefix - 1) + filesToSync[i][commonPrefix:])

	input('Press ENTER to sync files.')

	# After confirmation, push files to device
	for file in filesToSync:
		fromPath = os.path.join(os.path.normpath(MUSIC_DIR), os.path.normpath(file)[1:])
		toPath = posixpath.join(posixpath.normpath(PHONE_DIR), posixpath.normpath(file)[1:])

		adbCopy = subprocess.check_output([ADB_CMD, 'push', fromPath, toPath])
