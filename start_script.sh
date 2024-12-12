#!/bin/bash

SESSION_NAME="jettons_sender"

sender="jettons_bot/jettons_sender.py"
bot="jettons_bot"
web="jettons_bot/web.py"

python3 -m pip install -r requirements.txt

tmux new-session -d  $SESSION_NAME

# run sender
tmux send-keys -t $SESSION_NAME:0 "python3 $sender" C-m

# run bot
tmux new-window -t $SESSION_NAME:1 -n 'bot'
tmux send-keys -t $SESSION_NAME:1 "python3 $bot" C-m

# run web-server
tmux new-window -t $SESSION_NAME:2 -n 'web'
tmux send-keys -t $SESSION_NAME:2 "quart --app $web run --port=5000 --host=0.0.0.0" C-m

tmux attach-session -t $SESSION_NAME