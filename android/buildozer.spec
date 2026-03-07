[app]
title = Skate Rush
package.name = skaterush
package.domain = org.skaterush.game
source.dir = ..
source.include_exts = py,png,jpg,jpeg,wav,mp3,ttf,kv
version = 0.1.5
requirements = python3,kivy
orientation = landscape
fullscreen = 1
android.api = 35
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.release_artifact = aab
android.release_keystore = upload-keystore.jks
android.release_keyalias = upload
# Set passwords via environment variables before release build:
# P4A_RELEASE_KEYSTORE_PASSWD, P4A_RELEASE_KEYALIAS_PASSWD

# App icon/presplash.
icon.filename = ../assets/skaterush_logo.png
# presplash.filename = assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = /home/left/.buildozer_skaterush
bin_dir = /home/left/skate-main/android/bin
