#!/bin/bash
SCRIPT_DIR="$(cd $(dirname $(realpath "$0")) && pwd)"
source "${SCRIPT_DIR}/tmux_utils.sh"
# Initialize variables
env_file=""
bin_count=100
# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --env) env_file="$2"; shift ;;
        --bin-count) bin_count="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done
# Use the provided environment file or default to empty (headless mode)
if [ -n "$env_file" ]; then
    echo "Using environment file: $env_file"
else
    echo "No environment file specified. Running with default settings."
fi
cleanup_tmux() {
    tmux kill-session -t "vmtests"
}
trap cleanup_tmux EXIT
create_tmux_session_if_doesnt_exist "vmtests"
split_window "v"
split_window "h"
select_pane 0
split_window "h"
select_pane 0
# Start tilt with the specified environment or in headless mode
if [ -z "$env_file" ]; then
    tmux send-keys 'cd ~/rr_oks && tilt up -- --headless=true' C-m
else
    tmux send-keys "cd ~/rr_oks && tilt up --host 0.0.0.0 -- --headless=true --env_file $env_file" C-m
fi
echo "Waiting for services to start..."
sleep 60
select_pane 2
exec_command "htop"
select_pane 1
# Run generate_data.py with the specified bin_count and wait for 2 seconds before running the next scripts
tmux send-keys "cd ~/rr_oks_vm_scripts && python3 generate_data.py --csv-file \"${bin_count}_bins.csv\"" C-m
sleep 2
tmux send-keys "python3 upload_final.py ${bin_count}_bins.csv" C-m
tmux send-keys "python3 stow.py ${bin_count}_bins.csv" C-m
select_pane 3
exec_command "python3 stalldetector_dummy.py"
attach_to_session "vmtests"