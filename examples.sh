#!/bin/sh
# A launcher I use for the Pi Presents examples
# It is based on the one that launches Python Games; developed by Alex Bradbury
# with contributions from me

RET=0


while [ $RET -eq 0 ]; do
  GAME=$(zenity --width=700 --height=700 --list \
    --title="Pi Presents" \
    --text="Examples of Pi Presents in Operation, CTRL-BREAK to return" \
    --column="Example" --column="Description" \
    pp_mediashow_1p2 "A Repeating multi-media show for a Visitor Centre" \
    pp_interactive_1p2 "An Interactive Show for a Visitor Centre" \
    pp_exhibit_1p2 "Museum interpretation triggered by a button or PIR" \
    pp_menu_1p2 "Scrolling Menu Kiosk Content Chooser" \
    pp_radiobuttonshow_1p2 "Button operated Kiosk Content Chooser" \
    pp_hyperlinkshow_1p2 "A Touchscreen as seen in Museums" \
    pp_liveshow_1p2 "A multi-media show with dynamically provided content" \
    pp_presentation_1p2  "Controlling a multi-media show manually" \
    pp_audio_1p2 "Audio Capabilities" \
    pp_web_1p2 "Demonstration of Web Browser Player" \
    pp_concurrent_1p2 "Play two shows simultaneously" \
    pp_showcontrol_1p2 "Control one show from another" \
    pp_timeofday_1p2 "Run shows at specfied times each day" \
    pp_animate_1p2 "Demonstration of Animation Control" \
    pp_subshow_1p2 "Demonstration of Subshows" \
    pp_plugin_1p2 "Demonstration of Track Plugins" \
    pp_shutdown_1p2 "Shutdown the Raspberry Pi from Pi Presents" \
    website "pipresents.wordpress.com")
  RET=$?
  echo $RET
  if [ "$RET" -eq 0 ]
  then
     if [ "$GAME" = "website" ]
     then
        sensible-browser "http://pipresents.wordpress.com"
     else
       if [ "$GAME" != "" ]; then
          cd /home/pi/pipresents
          sudo python /home/pi/pipresents/pipresents.py -o /home/pi -p $GAME -bfg
       fi
     fi
  fi
done
