VERSION := $(shell python3 neoneo.py version)
RELEASE := build/neoneo-$(VERSION)

HELPER := build/neoneo-capslockdelay

.PHONY: test build helper dist icon install uninstall verify dump

test:
	python3 -m unittest discover -s tests -v

build:
	python3 neoneo.py build --out build

# Caps Lock delay helper: universal binary (Apple silicon + Intel), ad-hoc signed.
helper:
	mkdir -p build
	swiftc -O -target arm64-apple-macos11 -o "$(HELPER)-arm64" tools/capslockdelay.swift
	swiftc -O -target x86_64-apple-macos11 -o "$(HELPER)-x86_64" tools/capslockdelay.swift
	lipo -create -output "$(HELPER)" "$(HELPER)-arm64" "$(HELPER)-x86_64"
	codesign --force --sign - "$(HELPER)"

# Release folder and zip: build/neoneo-<version>{,.zip}
dist: helper
	python3 neoneo.py dist --out build --helper "$(HELPER)"
	rm -f "$(RELEASE).zip"
	cd build && ditto -c -k --norsrc --noextattr --noqtn --keepParent "neoneo-$(VERSION)" "neoneo-$(VERSION).zip"

# Regenerate layout/neoneo.icns (committed; only needed after changing the design).
icon:
	swift tools/make-icon.swift layout/neoneo.icns

# Same scripts as in the release zip.
install: dist
	sh "$(RELEASE)/install.sh"

uninstall:
	sh tools/uninstall.sh

# Compare the installed layout with the TSV.
verify:
	mkdir -p build
	swift tools/dump-layout.swift xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo > build/installed.tsv
	python3 neoneo.py verify build/installed.tsv

# make dump ID=com.apple.keylayout.German
dump:
	swift tools/dump-layout.swift $(ID)
