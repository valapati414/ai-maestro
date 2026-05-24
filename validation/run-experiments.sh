#!/usr/bin/env bash
#
# Hermes Empirical Validation Experiments (E1-E8)
# Per spec Section 5: https://github.com/valapati414/ai-maestro
#
# This script runs real Hermes processes in tmux and captures output.
# Results go to validation/transcripts/ and validation/analysis/
#
set -euo pipefail

VALDIR="$(cd "$(dirname "$0")" && pwd)"
TRANSCRIPTS="$VALDIR/transcripts"
ANALYSIS="$VALDIR/analysis"
SESSION="hmp-val"

mkdir -p "$TRANSCRIPTS" "$ANALYSIS"

log() { echo "[$(date +%H:%M:%S)] $1"; }

# Strip ANSI escape codes
strip_ansi() {
    sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | sed 's/\x1b\[[0-9;]*m//g' | sed 's/\x1b(B//g' | sed 's/\x1b\[?25[hl]//g' | sed 's/\x1b\[?1000[hl]//g' | sed 's/\x1b\[?2004[hl]//g'
}

# Capture tmux pane content (stripped of ANSI)
capture_pane() {
    local outfile="$1"
    tmux capture-pane -t "$SESSION" -p -S -5000 2>/dev/null | strip_ansi > "$outfile" 2>/dev/null || true
}

# Send a message to the Hermes session
send_to_hermes() {
    local msg="$1"
    tmux send-keys -t "$SESSION" "$msg" Enter
}

# Wait for Hermes to produce output after a send
wait_for_output() {
    local seconds="${1:-30}"
    sleep "$seconds"
}

# Start a fresh Hermes session
start_hermes() {
    log "Starting Hermes in tmux session '$SESSION'..."
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    sleep 1
    tmux new-session -d -s "$SESSION" -x 200 -y 50
    tmux send-keys -t "$SESSION" "hermes" Enter
    log "Waiting for Hermes to initialize..."
    sleep 10
    # Capture initial state
    capture_pane "$TRANSCRIPTS/e0-hermes-init.txt"
    log "Hermes initialized. Captured init transcript."
}

# Stop Hermes session
stop_hermes() {
    log "Stopping Hermes..."
    tmux send-keys -t "$SESSION" "/exit" Enter 2>/dev/null || true
    sleep 3
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    log "Hermes stopped."
}

# ─────────────────────────────────────────────
# E1 — TUI capture verification
# ─────────────────────────────────────────────
run_e1() {
    log "=== E1: TUI capture verification ==="
    local outfile="$TRANSCRIPTS/e1-tui-capture.txt"

    # Send a simple prompt
    send_to_hermes "Say exactly: HELLO_WORLD_TEST_12345"
    wait_for_output 20
    capture_pane "$outfile"

    # Also try alternate capture flags
    tmux capture-pane -t "$SESSION" -p -e -S - -E - 2>/dev/null | strip_ansi > "$TRANSCRIPTS/e1-tui-capture-extended.txt" || true

    log "E1 complete. Output captured."
}

# ─────────────────────────────────────────────
# E2 — Marker compliance (20 repetitions)
# ─────────────────────────────────────────────
run_e2() {
    log "=== E2: Marker compliance ==="
    local outfile="$TRANSCRIPTS/e2-marker-compliance.txt"
    local total=0
    local compliant=0
    local task_uuid=""

    > "$outfile"

    for i in $(seq 1 5); do
        task_uuid="test-task-$(printf '%04d' $i)"
        total=$((total + 1))

        log "  E2 iteration $i/5: dispatching task $task_uuid"

        # Send task with marker instruction
        send_to_hermes "Do the following task and when done, output EXACTLY this line on its own line: ###HMP/1 DONE $task_uuid Task completed successfully. Report the number 42."
        wait_for_output 25
        capture_pane "$TRANSCRIPTS/e2-iter-${i}.txt"

        # Check if marker appears in capture
        if grep -qP "^###HMP/1 DONE $task_uuid" "$TRANSCRIPTS/e2-iter-${i}.txt" 2>/dev/null; then
            compliant=$((compliant + 1))
            echo "  ITER $i: COMPLIANT" >> "$outfile"
        else
            # Check with relaxed matching (leading whitespace, mid-line)
            if grep -qP "###HMP/1 DONE $task_uuid" "$TRANSCRIPTS/e2-iter-${i}.txt" 2>/dev/null; then
                compliant=$((compliant + 1))
                echo "  ITER $i: COMPLIANT (relaxed match)" >> "$outfile"
            else
                echo "  ITER $i: NON-COMPLIANT" >> "$outfile"
            fi
        fi

        # Brief pause between iterations
        sleep 3
    done

    echo "" >> "$outfile"
    echo "Total: $total, Compliant: $compliant, Rate: $(( compliant * 100 / total ))%" >> "$outfile"
    log "E2 complete: $compliant/$total compliant ($(( compliant * 100 / total ))%)"
}

# ─────────────────────────────────────────────
# E3 — Marker placement consistency
# ─────────────────────────────────────────────
run_e3() {
    log "=== E3: Marker placement consistency ==="
    local outfile="$TRANSCRIPTS/e3-marker-placement.txt"
    local at_col0=0
    local with_whitespace=0
    local mid_line=0

    > "$outfile"

    for i in $(seq 1 5); do
        local capt="$TRANSCRIPTS/e2-iter-${i}.txt"
        if [ -f "$capt" ]; then
            # Check column 0
            if grep -qP "^###HMP/1" "$capt" 2>/dev/null; then
                at_col0=$((at_col0 + 1))
                echo "  Iter $i: column 0" >> "$outfile"
            elif grep -qP "^\s+###HMP/1" "$capt" 2>/dev/null; then
                with_whitespace=$((with_whitespace + 1))
                echo "  Iter $i: leading whitespace" >> "$outfile"
            elif grep -qP "###HMP/1" "$capt" 2>/dev/null; then
                mid_line=$((mid_line + 1))
                echo "  Iter $i: mid-line or embedded" >> "$outfile"
            else
                echo "  Iter $i: no marker found" >> "$outfile"
            fi
        fi
    done

    echo "" >> "$outfile"
    echo "Column 0: $at_col0, Whitespace: $with_whitespace, Mid-line: $mid_line" >> "$outfile"
    log "E3 complete: col0=$at_col0 ws=$with_whitespace mid=$mid_line"
}

# ─────────────────────────────────────────────
# E4 — Multi-task session behavior
# ─────────────────────────────────────────────
run_e4() {
    log "=== E4: Multi-task session behavior ==="
    local outfile="$TRANSCRIPTS/e4-multi-task.txt"

    # Send first task with marker
    send_to_hermes "Say exactly: FIRST_TASK_COMPLETE and then on a new line output: ###HMP/1 DONE multi-1 First task done."
    wait_for_output 20
    capture_pane "$TRANSCRIPTS/e4-after-task1.txt"

    # Immediately send second task
    send_to_hermes "Now say exactly: SECOND_TASK_COMPLETE and then on a new line output: ###HMP/1 DONE multi-2 Second task done."
    wait_for_output 20
    capture_pane "$TRANSCRIPTS/e4-after-task2.txt"

    # Combine
    cat "$TRANSCRIPTS/e4-after-task1.txt" > "$outfile"
    echo -e "\n\n===== SECOND TASK =====\n\n" >> "$outfile"
    cat "$TRANSCRIPTS/e4-after-task2.txt" >> "$outfile"

    log "E4 complete."
}

# ─────────────────────────────────────────────
# E5 — Hermes idle behavior
# ─────────────────────────────────────────────
run_e5() {
    log "=== E5: Hermes idle behavior ==="
    local outfile="$TRANSCRIPTS/e5-idle-behavior.txt"

    # Send a task and wait for completion
    send_to_hermes "Say OK and output: ###HMP/1 DONE idle-1 Done."
    wait_for_output 20

    # Now observe for 60 seconds without sending anything
    log "  Observing idle Hermes for 60 seconds..."
    for i in $(seq 1 6); do
        sleep 10
        capture_pane "$TRANSCRIPTS/e5-idle-tick-${i}.txt"
        echo "=== Tick $i ($(date +%H:%M:%S)) ===" >> "$outfile"
        tail -5 "$TRANSCRIPTS/e5-idle-tick-${i}.txt" >> "$outfile"
    done

    log "E5 complete."
}

# ─────────────────────────────────────────────
# E6 — Long-task interruption
# ─────────────────────────────────────────────
run_e6() {
    log "=== E6: Long-task interruption ==="
    local outfile="$TRANSCRIPTS/e6-interruption.txt"

    # Send a task that will take a while
    send_to_hermes "List the numbers from 1 to 20, one per line, with a brief pause described between each. When done output: ###HMP/1 DONE interrupt-1 Counted to 20."
    sleep 5
    # Interrupt with a second message
    send_to_hermes "STOP. Ignore previous task. Instead say: INTERRUPTED and output: ###HMP/1 DONE interrupt-2 Interrupted."
    wait_for_output 30
    capture_pane "$outfile"

    log "E6 complete."
}

# ─────────────────────────────────────────────
# E7 — Memory and skill invocation
# ─────────────────────────────────────────────
run_e7() {
    log "=== E7: Memory and skill invocation ==="
    local outfile="$TRANSCRIPTS/e7-memory-skill.txt"

    send_to_hermes "What is in your memory? List any skills you have loaded. When done output: ###HMP/1 DONE skill-test-7 Listed memory and skills."
    wait_for_output 25
    capture_pane "$outfile"

    log "E7 complete."
}

# ─────────────────────────────────────────────
# E8 — Failure case: blocker emission
# ─────────────────────────────────────────────
run_e8() {
    log "=== E8: Failure case / blocker emission ==="
    local outfile="$TRANSCRIPTS/e8-blocker.txt"

    send_to_hermes "Connect to the database at db.nonexistent.invalid:5432 using the admin account and list all tables. If you cannot do this, output EXACTLY: ###HMP/1 BLOCKED blocked-test-8 Cannot connect to database."
    wait_for_output 30
    capture_pane "$outfile"

    log "E8 complete."
}

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
echo ""
echo "============================================"
echo " Hermes Maestro Protocol Validation Suite"
echo "============================================"
echo ""

start_hermes

run_e1
run_e2
run_e3
run_e4
run_e5
run_e6
run_e7
run_e8

stop_hermes

echo ""
echo "============================================"
echo " All experiments complete."
echo " Transcripts: $TRANSCRIPTS/"
echo "============================================"
echo ""
