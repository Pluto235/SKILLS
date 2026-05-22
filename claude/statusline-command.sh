#!/bin/bash

input=$(cat)

# ── Colors ────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
BCYAN="\033[1;36m"
GREEN="\033[32m"
BGREEN="\033[1;32m"
YELLOW="\033[33m"
BYELLOW="\033[1;33m"
MAGENTA="\033[35m"
BMAGENTA="\033[1;35m"
BLUE="\033[34m"
BBLUE="\033[1;34m"
RED="\033[31m"
BRED="\033[1;31m"
WHITE="\033[37m"
BWHITE="\033[1;37m"
GRAY="\033[90m"

# ── Raw data ──────────────────────────────────────────────
model=$(echo "$input"      | jq -r '.model.display_name // "Unknown"')
used_pct=$(echo "$input"   | jq -r '.context_window.used_percentage // empty')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input"| jq -r '.context_window.total_output_tokens // 0')
total_tokens=$((total_input + total_output))
five_pct=$(echo "$input"   | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_resets=$(echo "$input"| jq -r '.rate_limits.five_hour.resets_at // empty')
seven_pct=$(echo "$input"  | jq -r '.rate_limits.seven_day.used_percentage // empty')
cwd=$(echo "$input"        | jq -r '.cwd // .workspace.current_dir // ""')

# ── Abbreviate home dir ────────────────────────────────────
home_dir="$HOME"
if [ -n "$home_dir" ] && [ "${cwd#$home_dir}" != "$cwd" ]; then
  cwd="~${cwd#$home_dir}"
fi

# ── Progress bar (10 chars) ────────────────────────────────
build_bar() {
  local pct="$1" width=10
  local filled empty bar=""
  if [ -n "$pct" ]; then
    filled=$(echo "$pct $width" | awk '{printf "%d", int($1 * $2 / 100 + 0.5)}')
    [ "$filled" -gt "$width" ] && filled=$width
    empty=$(( width - filled ))
    for i in $(seq 1 $filled 2>/dev/null); do bar="${bar}█"; done
    for i in $(seq 1 $empty  2>/dev/null); do bar="${bar}░"; done
  else
    for i in $(seq 1 $width  2>/dev/null); do bar="${bar}░"; done
  fi
  echo "$bar"
}

ctx_bar=$(build_bar "$used_pct")

# Pick bar color based on usage level
if [ -n "$used_pct" ]; then
  ctx_label=$(printf "%.0f%%" "$used_pct")
  pct_int=$(printf "%.0f" "$used_pct")
  if   [ "$pct_int" -ge 85 ]; then bar_color="$BRED"
  elif [ "$pct_int" -ge 60 ]; then bar_color="$BYELLOW"
  else                              bar_color="$BGREEN"
  fi
else
  ctx_label="--"
  bar_color="$GRAY"
fi

# ── Session tokens ─────────────────────────────────────────
if [ "$total_tokens" -gt 0 ]; then
  token_str=$(echo "$total_tokens" | awk '{
    if ($1 >= 1000000) printf "%.1fM", $1/1000000
    else if ($1 >= 1000) printf "%.1fk", $1/1000
    else printf "%d", $1
  }')
else
  token_str="--"
fi

# ── 5-hour limit ───────────────────────────────────────────
if [ -n "$five_pct" ]; then
  five_label=$(printf "%.0f%%" "$five_pct")
  five_int=$(printf "%.0f" "$five_pct")
  if   [ "$five_int" -ge 85 ]; then five_color="$BRED"
  elif [ "$five_int" -ge 60 ]; then five_color="$BYELLOW"
  else                               five_color="$GREEN"
  fi

  if [ -n "$five_resets" ]; then
    now=$(date +%s)
    diff=$(( five_resets - now ))
    if [ "$diff" -le 0 ]; then
      reset_str="resets now"
    else
      mins=$(( diff / 60 ))
      hrs=$(( mins / 60 ))
      rmins=$(( mins % 60 ))
      if [ "$hrs" -gt 0 ]; then
        reset_str=$(printf "%dh %02dm" "$hrs" "$rmins")
      else
        reset_str=$(printf "%dm" "$mins")
      fi
    fi
  else
    reset_str=""
  fi
  have_five=1
else
  have_five=0
fi

# ── 7-day limit ────────────────────────────────────────────
if [ -n "$seven_pct" ]; then
  seven_label=$(printf "%.0f%%" "$seven_pct")
  seven_int=$(printf "%.0f" "$seven_pct")
  if   [ "$seven_int" -ge 85 ]; then seven_color="$BRED"
  elif [ "$seven_int" -ge 60 ]; then seven_color="$BYELLOW"
  else                                seven_color="$GREEN"
  fi
  have_seven=1
else
  have_seven=0
fi

# ══════════════════════════════════════════════════════════
#  Layout  (single line)
#
#  model │ bar used% · tokens │ 5h% ↺reset │ 7d% │ cwd
# ══════════════════════════════════════════════════════════

SEP="${GRAY} │ ${RESET}"
DOT="${GRAY} · ${RESET}"

# ── user@host (from PS1) ───────────────────────────────────
printf "${BGREEN}%s${RESET}${GRAY}@${RESET}${BGREEN}%s${RESET}" "$(whoami)" "$(hostname -s)"
printf "${SEP}"

# ── Model ─────────────────────────────────────────────────
printf "${BCYAN}%s${RESET}" "$model"
printf "${SEP}"

# ── Context bar + used% · session tokens ──────────────────
printf "${bar_color}%s${RESET}" "$ctx_bar"
printf " ${BWHITE}%s${RESET}" "$ctx_label"
printf "${DOT}"
printf "${DIM}tok${RESET} ${MAGENTA}%s${RESET}" "$token_str"
printf "${SEP}"

# ── 5-hour limit ──────────────────────────────────────────
if [ "$have_five" -eq 1 ]; then
  printf "${DIM}5h${RESET} ${five_color}%s${RESET}" "$five_label"
  if [ -n "$reset_str" ]; then
    printf " ${GRAY}↺%s${RESET}" "$reset_str"
  fi
else
  printf "${GRAY}5h --${RESET}"
fi
printf "${SEP}"

# ── 7-day limit ───────────────────────────────────────────
if [ "$have_seven" -eq 1 ]; then
  printf "${DIM}7d${RESET} ${seven_color}%s${RESET}" "$seven_label"
else
  printf "${GRAY}7d --${RESET}"
fi
printf "${SEP}"

# ── Current working directory (truncate to 40 chars) ──────
if [ "${#cwd}" -gt 40 ]; then
  cwd="...${cwd: -37}"
fi
printf "${BBLUE}%s${RESET}" "$cwd"

# ── Git branch ────────────────────────────────────────────
git_branch=$(git -C "$(echo "$input" | jq -r '.cwd // .workspace.current_dir // ""')" \
  --no-optional-locks branch --show-current 2>/dev/null)
if [ -n "$git_branch" ]; then
  printf "${SEP}"
  printf "${BYELLOW} %s${RESET}" "$git_branch"
fi

printf "\n"
