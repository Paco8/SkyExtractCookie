# SkyExtractCookie

SkyExtractCookie is a complementary program for the [plugin.video.skyott addon](https://github.com/Paco8/plugin.video.skyott). This program allows you to obtain a *.key file in order to log in to `plugin.video.skyott`.

The program will open a Google Chrome window (Chromium or Brave also work) with the streaming service website, where you will need to log in. Once that's done, the program will obtain a token from the website, close the Chrome window, and save that token in a file on your disk.

This key file can be used to log in to `plugin.video.skyott`. You can use the key file on multiple devices.

## Download
There are versions for [Windows](https://github.com/Paco8/SkyExtractCookie/releases/download/v1.0.1/SkyExtractCookie-1.0.1-windows.zip), [Linux](https://github.com/Paco8/SkyExtractCookie/releases/download/v1.0.1/SkyExtractCookie-1.0.1-xenial.zip) y [Mac OS](https://github.com/Paco8/SkyExtractCookie/releases/download/v1.0.1/SkyExtractCookie-1.0.1-macos.zip).

### Instructions for Use
- Unzip the downloaded file. The zip contains two files, `SkyExtractCookie` which is the executable, and `settings.json`.
- Run the `SkyExtractCookie` file. After a welcome message, it will ask you to press Enter, after which it will open a Google Chrome window in incognito mode with the streaming service website.
- In that window, select the Identify option and enter your credentials.
- If everything went well, the Chrome window will close, and the token will be saved in the same folder in the file `skyauthentication.key`.
- Copy this file to the device where you want to use it, in a folder that is accessible by Kodi (for example, `Download`).
- In Kodi, go to `plugin.video.skyott` and select `Log in with a key file`. If everything went well, the main menu will load, and you can access the different sections.
