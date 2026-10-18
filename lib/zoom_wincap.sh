#!/bin/zsh
# capture the Zoom Meeting window every 3 s while the meeting runs; re-resolve the window id each minute
S=$1; R=$2; i=0; wid=""
while pgrep -q CptHost; do
  if (( i % 20 == 0 )) || [[ -z $wid ]]; then wid=$(swift ${0:A:h}/zoom_window.swift 2>/dev/null | awk '/^BEST/{print $2}'); fi
  [[ -n $wid && $wid != 0 ]] && screencapture -x -o -l$wid -t jpg $R/win/$(date +%H%M%S).jpg 2>/dev/null
  i=$((i+1)); sleep 3
done
