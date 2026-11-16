// Registers a .keylayout in ~/Library/Keyboard Layouts with the Text Input
// system so it can be added without logging out. Bundles are not picked up
// this way; only standalone .keylayout files are.
import Carbon

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write("usage: register-layout.swift <path.keylayout>\n".data(using: .utf8)!)
    exit(2)
}
let status = TISRegisterInputSource(URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL)
guard status == noErr else {
    FileHandle.standardError.write("TISRegisterInputSource failed: \(status)\n".data(using: .utf8)!)
    exit(1)
}
