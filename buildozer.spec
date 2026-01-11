[app]

# (str) Title of your application
title = Diary App

# (str) Package name
package.name = diaryapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js,ttf,mp3,wav

# (list) List of exclusions using pattern matching
source.exclude_patterns = assets/cache/*, bin/*, .git/*, .github/*, __pycache__/*

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,plyer,mutagen,pyjnius,android

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_FINE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 19b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (str) Android additional libraries to copy into libs/armeabi
#android.add_libs_armeabi = libs/android/*.so
#android.add_libs_armeabi_v7a = libs/android-v7a/*.so
#android.add_libs_arm64_v8a = libs/android-v8a/*.so
#android.add_libs_x86 = libs/android-x86/*.so
#android.add_libs_mips = libs/android-mips/*.so

# (bool) Indicate whether the screen should stay on
# Don't forget to add the WAKE_LOCK permission if you set this to True
#android.wakelock = False

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (list) Android library project to add (will be added in the
# project.properties automatically.)
#android.library_references =

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) Android apptheme
#android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Android gradle dependencies
#android.gradle_dependencies =

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package, or any package that references AndroidX.
#android.enable_androidx = True

# (list) Java classes to add
#android.add_src =

# (list) Java jar files to add
#android.add_jars =

# (list) Java files to add
#android.add_src =

# (list) AAR files to add
#android.add_aars =

# (list) Gradle dependencies to add
#android.gradle_dependencies =

# (list) Activities to add
#android.add_activities =

# (list) Native libraries to add
#android.add_libs_armeabi =

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (int) Port number to specify an explicit --port= p4a argument (eg for bootstrap flask)
#p4a.port =


#
# Python for android (p4a) specific
#

# (str) python-for-android git url
#p4a.source_dir =

# (str) python-for-android local directory
#p4a.local_recipes =

# (str) python-for-android hook directory
#p4a.hook_dir =

# (str) python-for-android remote directory (if linked manually)
#p4a.remote_links =

# (str) python-for-android git branch to use
#p4a.branch = master

# (str) python-for-android bootstrap to use
#p4a.bootstrap = sdl2


#
# iOS specific
#

# (str) Path to the toolchain script
#ios.toolchain_path = ./toolchain.sh

# (str) Xcode project name
#ios.kivy_ios_url = https://github.com/kivy/kivy-ios
#ios.kivy_ios_branch = master

# (str) Xcode verbose logging
#ios.verbose = 1

# (str) Xcode codesign
#ios.codesign.allowed = false


#
# Buildozer specific
#

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output storage, absolute or relative to spec file
# bin_dir = ./bin

# (str) Patterns to exclude from the gitignore
# build_dir_excludes = .git, .github

# (str) Patterns to exclude from the gitignore
# bin_dir_excludes = .git, .github

# (str) Patterns to exclude from the gitignore
# global_excludes = .git, .github
