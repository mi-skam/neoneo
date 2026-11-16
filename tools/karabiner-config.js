// Add or remove the neoneo rules in Karabiner-Elements' karabiner.json.
// JavaScript for Automation, so it runs on any Mac without extra tools.
//
// usage: osascript -l JavaScript karabiner-config.js install RULES_JSON KARABINER_JSON
//        osascript -l JavaScript karabiner-config.js uninstall KARABINER_JSON
//
// install: replaces the neoneo rules (descriptions starting "neoneo:") in the
// selected profile, placing them first, and turns off "Manipulate caps lock
// LED" for the keyboards named in the rules' device conditions (the measured
// Apple keyboards), so the LED does not light while Mod3 is held.
// uninstall: removes the neoneo rules from every profile; device settings stay.
// Karabiner-Elements reloads karabiner.json by itself when it changes.
ObjC.import("Foundation");

const PREFIX = "neoneo:";

function read(path) {
    const text = $.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null);
    if (text.isNil()) throw new Error(`cannot read ${path}`);
    return JSON.parse(text.js);
}

function write(path, data) {
    const text = $(JSON.stringify(data, null, 4) + "\n");
    if (!text.writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null)) {
        throw new Error(`cannot write ${path}`);
    }
}

function isNeoneo(rule) {
    return rule.description.startsWith(PREFIX);
}

function withoutNeoneo(profile) {
    const mods = profile.complex_modifications;
    if (!mods || !mods.rules) return 0;
    const before = mods.rules.length;
    mods.rules = mods.rules.filter((r) => !isNeoneo(r));
    return before - mods.rules.length;
}

// Device identifiers from the rules' device_if conditions.
function ledDevices(rules) {
    const seen = new Map();
    for (const rule of rules) {
        for (const m of rule.manipulators) {
            for (const c of m.conditions) {
                if (c.type !== "device_if") continue;
                for (const id of c.identifiers) seen.set(`${id.vendor_id}/${id.product_id}`, id);
            }
        }
    }
    return [...seen.values()];
}

function setLedOff(profile, ident) {
    if (!profile.devices) profile.devices = [];
    let entry = profile.devices.find((d) =>
        d.identifiers.vendor_id === ident.vendor_id && d.identifiers.product_id === ident.product_id);
    if (!entry) {
        entry = { identifiers: { is_keyboard: true, vendor_id: ident.vendor_id, product_id: ident.product_id } };
        profile.devices.push(entry);
    }
    entry.manipulate_caps_lock_led = false;
}

function install(rulesPath, configPath) {
    const rules = read(rulesPath).rules;
    const data = read(configPath);
    const profile = data.profiles.find((p) => p.selected);
    if (!profile) throw new Error(`no selected profile in ${configPath}`);
    if (!profile.complex_modifications) profile.complex_modifications = {};
    if (!profile.complex_modifications.rules) profile.complex_modifications.rules = [];
    withoutNeoneo(profile);
    profile.complex_modifications.rules.unshift(...rules);
    const devices = ledDevices(rules);
    devices.forEach((d) => setLedOff(profile, d));
    write(configPath, data);
    return `Karabiner: ${rules.length} neoneo rules in profile "${profile.name}", ` +
        `caps lock LED off for ${devices.length} keyboards`;
}

function uninstall(configPath) {
    const data = read(configPath);
    const removed = data.profiles.reduce((n, p) => n + withoutNeoneo(p), 0);
    write(configPath, data);
    return `Karabiner: removed ${removed} neoneo rules`;
}

function run(argv) {
    if (argv[0] === "install" && argv.length === 3) return install(argv[1], argv[2]);
    if (argv[0] === "uninstall" && argv.length === 2) return uninstall(argv[1]);
    throw new Error("usage: karabiner-config.js install RULES_JSON KARABINER_JSON | uninstall KARABINER_JSON");
}
