LAYOUTS := $(HOME)/Library/Keyboard Layouts
KARABINER := $(HOME)/.config/karabiner/assets/complex_modifications
BUNDLE := $(LAYOUTS)/neoneo.bundle
AGENT := $(HOME)/Library/LaunchAgents/neoneo.capslockdelay.plist

.PHONY: test build icon install uninstall verify dump

test:
	python3 -m unittest discover -s tests -v

build:
	python3 neoneo.py build --out build

# Regenerate layout/neoneo.icns (committed; only needed after changing the design).
icon:
	swift tools/make-icon.swift layout/neoneo.icns

install: build
	mkdir -p "$(LAYOUTS)" "$(KARABINER)"
	cp -R build/neoneo.bundle "$(LAYOUTS)/"
	cp build/karabiner-neoneo.json "$(KARABINER)/neoneo.json"
	python3 tools/enabled-sources.py add neoneo -24601
	cp tools/neoneo.capslockdelay.plist "$(AGENT)"
	-launchctl bootout gui/$$(id -u) "$(AGENT)" 2>/dev/null
	launchctl bootstrap gui/$$(id -u) "$(AGENT)"
	@echo "Installed. Log out and in, select 'neoneo' in the input menu,"
	@echo "then enable both 'neoneo' rules in Karabiner > Complex Modifications."

uninstall:
	swift tools/select-layout.swift com.apple.keylayout.German
	rm -r "$(BUNDLE)"
	rm "$(KARABINER)/neoneo.json"
	python3 tools/enabled-sources.py remove neoneo
	launchctl bootout gui/$$(id -u) "$(AGENT)"
	rm "$(AGENT)"
	@echo "Removed. Remove the 'neoneo' rules in Karabiner, then log out and in."

# Compare the installed layout with the TSV.
verify:
	mkdir -p build
	swift tools/dump-layout.swift xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo > build/installed.tsv
	python3 neoneo.py verify build/installed.tsv

# make dump ID=com.apple.keylayout.German
dump:
	swift tools/dump-layout.swift $(ID)
