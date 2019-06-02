#!/bin/sh
#
# Setup a session called `ReBalancer` with two horizontally split up windows
#
SESSION_NAME="ReBalancer"
# set up tmux
tmux start-server
# create a new tmux session
tmux new-session -d -s $SESSION_NAME
# start nano editor with settings
tmux send-keys "nano _settings.py" C-m
# split window horizontally  on 70 percent of the screen
# and start our script, -d return focus to previous window
tmux split-window -dh -p 70 'python run.py; read'
# return to main window
tmux select-window -t $SESSION_NAME:0
# finished setup, attach to the tmux session!
tmux attach-session -t $SESSION_NAME:0
