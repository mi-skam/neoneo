LAYOUTS := $(HOME)/Library/Keyboard Layouts
KARABINER := $(HOME)/.config/karabiner/assets/complex_modifications
LAYOUT := $(LAYOUTS)/neoneo.keylayout
AGENT := $(HOME)/Library/LaunchAgents/neoneo.capslockdelay.plist

.PHONY: test build install uninstall verify dump

test:
	python3 -m unittest discover -s tests -v

build:
	python3 neoneo.py build --out build

install: build
	mkdir -p "$(LAYOUTS)" "$(KARABINER)"
	cp build/neoneo.keylayout "$(LAYOUT)"
	cp build/karabiner-neoneo.json "$(KARABINER)/neoneo.json"
	swift tools/register-layout.swift "$(LAYOUT)"
	python3 tools/enabled-sources.py add neoneo -24601
	cp tools/neoneo.capslockdelay.plist "$(AGENT)"
	-launchctl bootout gui/$$(id -u) "$(AGENT)" 2>/dev/null
	launchctl bootstrap gui/$$(id -u) "$(AGENT)"
	@echo "Installed. Log out and in, select 'neoneo' in the input menu,"
	@echo "then enable both 'neoneo' rules in Karabiner > Complex Modifications."

uninstall:
	rm "$(LAYOUT)"
	rm "$(KARABINER)/neoneo.json"
	python3 tools/enabled-sources.py remove neoneo
	launchctl bootout gui/$$(id -u) "$(AGENT)"
	rm "$(AGENT)"
	@echo "Removed. Remove the 'neoneo' rules in Karabiner, then log out and in."

# Compare the installed layout with the TSV.
verify:
	mkdir -p build
	swift tools/dump-layout.swift org.unknown.keylayout.neoneo > build/installed.tsv
	python3 neoneo.py verify build/installed.tsv

# make dump ID=com.apple.keylayout.German
dump:
	swift tools/dump-layout.swift $(ID)
