#!/usr/bin/env bash

set -Eeo pipefail

_is_sourced() {
	# https://unix.stackexchange.com/a/215279
	[ "${#FUNCNAME[@]}" -ge 2 ] \
		&& [ "${FUNCNAME[0]}" = '_is_sourced' ] \
		&& [ "${FUNCNAME[1]}" = 'source' ]
}


run_startup_scripts() {
	printf '\n'
	local f
	for f; do
		case "$f" in
			*.sh)
				if [ -x "$f" ]; then
					printf '%s: running %s\n' "$0" "$f"
					"$f"
				else
					printf '%s: sourcing %s\n' "$0" "$f"
					. "$f"
				fi
				;;
		esac
		printf '\n'
	done
}


_main() {
  run_startup_scripts /docker-startup-script/*
  exec "$@"
}

if ! _is_sourced; then
	_main "$@"
fi
