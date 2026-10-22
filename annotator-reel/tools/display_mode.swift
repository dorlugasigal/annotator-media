// Usage: display_mode <name-fragment> get | set <ioDisplayModeID>
// Changes one display for the current login session only (kCGConfigureForSession).
import AppKit
import CoreGraphics
let args = CommandLine.arguments
guard args.count >= 3 else { fputs("usage: display_mode <name> get | set <id>\n", stderr); exit(2) }
guard let screen = NSScreen.screens.first(where: { $0.localizedName.localizedCaseInsensitiveContains(args[1]) }),
      let number = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else {
    fputs("display matching \(args[1]) not found\n", stderr); exit(1)
}
let id = CGDirectDisplayID(number.uint32Value)
let current = CGDisplayCopyDisplayMode(id)!
if args[2] == "get" {
    print("\(current.ioDisplayModeID) \(current.width)x\(current.height)pt \(current.pixelWidth)x\(current.pixelHeight)px \(Int(current.refreshRate))Hz")
    exit(0)
}
guard args.count == 4, args[2] == "set", let target = Int32(args[3]) else { fputs("usage: display_mode <name> set <id>\n", stderr); exit(2) }
let opts = [kCGDisplayShowDuplicateLowResolutionModes: kCFBooleanTrue] as CFDictionary
guard let modes = CGDisplayCopyAllDisplayModes(id, opts) as? [CGDisplayMode],
      let mode = modes.first(where: { $0.ioDisplayModeID == target }) else { fputs("mode \(target) not found\n", stderr); exit(1) }
var config: CGDisplayConfigRef?
guard CGBeginDisplayConfiguration(&config) == .success else { exit(1) }
CGConfigureDisplayWithDisplayMode(config, id, mode, nil)
guard CGCompleteDisplayConfiguration(config, .forSession) == .success else { fputs("configuration failed\n", stderr); exit(1) }
print("set \(mode.ioDisplayModeID) \(mode.width)x\(mode.height)pt \(mode.pixelWidth)x\(mode.pixelHeight)px")
