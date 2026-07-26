#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

output="Virtual-1"

get_current_resolution() {
  xrandr --current |
    awk -v output="$output" '
      $1 == output {
        for (i = 1; i <= NF; i++) {
          if ($i ~ /^[0-9]+x[0-9]+\+[0-9]+\+[0-9]+$/) {
            split($i, parts, "+")
            print parts[1]
            exit
          }
        }
      }
    '
}

get_available_resolutions() {
  xrandr --query |
    awk -v output="$output" '
      $1 == output { active = 1; next }
      active && $1 ~ /^[0-9]+x[0-9]+$/ {
        if (!seen[$1]++) print $1
        next
      }
      active { exit }
    '
}

mapfile -t resolutions < <(get_available_resolutions)

if ((${#resolutions[@]} == 0)); then
  echo "Nessuna risoluzione disponibile per $output."
  exit 1
fi

while true; do
  current="$(get_current_resolution)"

  clear
  echo "Cambio risoluzione VMware"
  echo "Risoluzione attuale: $current"
  echo

  for i in "${!resolutions[@]}"; do
    marker=" "
    [[ "${resolutions[$i]}" == "$current" ]] && marker="*"
    printf '%2d) %s %s\n' "$((i + 1))" "$marker" "${resolutions[$i]}"
  done

  echo
  echo " q) Esci"
  read -r -p "Scegli una risoluzione: " choice

  [[ "${choice,,}" == "q" ]] && exit 0

  if [[ ! "$choice" =~ ^[0-9]+$ ]] ||
     ((10#$choice < 1 || 10#$choice > ${#resolutions[@]})); then
    read -r -p "Scelta non valida. Premi Invio per riprovare." _
    continue
  fi

  selected="${resolutions[$((10#$choice - 1))]}"
  if [[ "$selected" == "$current" ]]; then
    read -r -p "Questa risoluzione è già attiva. Premi Invio." _
    continue
  fi

  xrandr --output "$output" --mode "$selected"
  echo
  echo "Risoluzione impostata a $selected."
  echo "Conferma entro 15 secondi, altrimenti torno a $current."

  answer=""
  if read -r -t 15 -p "Vuoi mantenerla? [s/N] " answer &&
     [[ "${answer,,}" == "s" || "${answer,,}" == "si" ||
        "${answer,,}" == "sì" || "${answer,,}" == "y" ||
        "${answer,,}" == "yes" ]]; then
    echo "Risoluzione confermata."
    sleep 1
  else
    echo
    echo "Ripristino $current..."
    xrandr --output "$output" --mode "$current"
    sleep 1
  fi
done
