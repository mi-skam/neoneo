// neoneo-capslockdelay: keeps macOS's Caps Lock delay off for Karabiner's
// virtual keyboard.
//
// macOS delays Caps Lock on Apple-vendor keyboards; Karabiner's virtual
// keyboard reports Apple's vendor id, so without this a fast Mod3+key types
// the layer-1 character. The setting belongs to the device and is lost
// whenever Karabiner (re)creates it: at login, on Karabiner restarts and
// updates.
//
// launchd starts this helper through an IOKit-matching launch event each time
// the virtual keyboard appears (see neoneo.capslockdelay.plist). The helper
// must take the event from the stream, or launchd relaunches it every 10 s.
// It applies the setting, repeats it twice in case the device's event service
// shows up a moment later, and exits; it uses nothing between events.
import Foundation
import XPC

let matching = #"{"ProductID":0x250,"VendorID":0x5ac}"#
let setting = #"{"CapsLockDelayOverride":0}"#

func apply() {
    let hidutil = Process()
    hidutil.executableURL = URL(fileURLWithPath: "/usr/bin/hidutil")
    hidutil.arguments = ["property", "--matching", matching, "--set", setting]
    hidutil.standardOutput = FileHandle.nullDevice
    do {
        try hidutil.run()
        hidutil.waitUntilExit()
    } catch {
        FileHandle.standardError.write("neoneo-capslockdelay: \(error)\n".data(using: .utf8)!)
        exit(1)
    }
}

var lastEvent = Date()

xpc_set_event_stream_handler("com.apple.iokit.matching", DispatchQueue.main) { _ in
    lastEvent = Date()
    apply()
    for delay in [1.0, 3.0] {
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) { apply() }
    }
}

// Exit once no event has arrived for 5 s (after the delayed repeats).
func exitWhenIdle() {
    DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
        if Date().timeIntervalSince(lastEvent) >= 5 { exit(0) }
        exitWhenIdle()
    }
}
exitWhenIdle()
dispatchMain()
