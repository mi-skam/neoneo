LAYOUTS := $(HOME)/Library/Keyboard Layouts
KARABINER := $(HOME)/.config/karabiner/assets/complex_modifications
LAYOUT := $(LAYOUTS)/neoneo.keylayout
SPIKE_LAYOUT := $(LAYOUTS)/neoneo-spike.keylayout

.PHONY: test build install uninstall verify dump spike-install spike-uninstall

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
	@echo "Installed. Log out and in, select 'neoneo' in the input menu,"
	@echo "then enable both 'neoneo' rules in Karabiner > Complex Modifications."

uninstall:
	rm "$(LAYOUT)"
	rm "$(KARABINER)/neoneo.json"
	python3 tools/enabled-sources.py remove neoneo
	@echo "Removed. Remove the 'neoneo' rules in Karabiner, then log out and in."

# Compare the installed layout with the TSV.
verify:
	mkdir -p build
	swift tools/dump-layout.swift org.unknown.keylayout.neoneo > build/installed.tsv
	python3 neoneo.py verify build/installed.tsv

# make dump ID=com.apple.keylayout.German
dump:
	swift tools/dump-layout.swift $(ID)

spike-install:
	mkdir -p "$(LAYOUTS)" "$(KARABINER)"
	cp spike/neoneo-spike.keylayout "$(SPIKE_LAYOUT)"
	cp spike/karabiner-neoneo-spike.json "$(KARABINER)/neoneo-spike.json"
	swift tools/register-layout.swift "$(SPIKE_LAYOUT)"
	@echo "Installed. Add the input source 'neoneo-spike' (listed under Others),"
	@echo "then enable 'neoneo spike' rules in Karabiner > Complex Modifications."

spike-uninstall:
	rm "$(SPIKE_LAYOUT)"
	rm "$(KARABINER)/neoneo-spike.json"
	@echo "Removed. Remove the input source and the Karabiner rules in their settings, then log out and in."
