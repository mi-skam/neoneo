// Selects an installed input source by id.
//
// usage: swift tools/select-layout.swift <input-source-id>
//
// `make uninstall` runs this with Apple's German layout before removing the
// neoneo bundle: deleting the selected layout's files makes every app crash
// when it is activated (HIToolbox _TSMSetInputSourceSelected on a NULL id).
import Carbon

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write("usage: select-layout.swift <input-source-id>\n".data(using: .utf8)!)
    exit(2)
}
let id = CommandLine.arguments[1]
let filter = [kTISPropertyInputSourceID as String: id] as CFDictionary
guard let source = (TISCreateInputSourceList(filter, false).takeRetainedValue() as! [TISInputSource]).first else {
    FileHandle.standardError.write("input source not enabled: \(id)\n".data(using: .utf8)!)
    exit(1)
}
let status = TISSelectInputSource(source)
guard status == noErr else {
    FileHandle.standardError.write("TISSelectInputSource failed: \(status)\n".data(using: .utf8)!)
    exit(1)
}
