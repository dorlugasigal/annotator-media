#!/usr/bin/env bash
# Owner-run: records the reel takes on the DeskPad virtual display at HiDPI (1920x1080 pt, 3840x2160 px).
# Only the DeskPad display changes mode; it is restored on exit. The main display is never touched.
set -uo pipefail
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
tool=/tmp/reel-display/display_mode
screen="${ANNOTATOR_REEL_SCREEN:-DeskPad}"
original="$($tool "$screen" get | cut -d' ' -f1)" || { echo "Open DeskPad first."; exit 1; }
restore() { "$tool" "$screen" set "$original" >/dev/null && echo "restored $screen mode $original"; }
trap restore EXIT
"$tool" "$screen" set "${REEL_HIDPI_MODE:-24}"
sleep 2
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
take_env=()
if [[ -n "${1:-}" ]]; then take_env=(ANNOTATOR_REEL_TAKE="$1" TEST_RUNNER_ANNOTATOR_REEL_TAKE="$1"); fi
env ANNOTATOR_RECORD_REEL=1 TEST_RUNNER_ANNOTATOR_RECORD_REEL=1 \
  ANNOTATOR_REEL_SCREEN="$screen" TEST_RUNNER_ANNOTATOR_REEL_SCREEN="$screen" "${take_env[@]}" \
  xcodebuild -project "$repo/apps/macos/Annotator.xcodeproj" -scheme Annotator -configuration Debug \
  -destination 'platform=macOS,arch=arm64' -derivedDataPath "$repo/build/ReelRecordingSigned" \
  CODE_SIGN_STYLE=Manual CODE_SIGN_IDENTITY="Apple Development" CODE_SIGNING_REQUIRED=YES DEVELOPMENT_TEAM="${DEVELOPMENT_TEAM:-NK959D954Y}" \
  -only-testing:NativeAppTests/ReelRecordingTests test-without-building
