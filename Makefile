LAYOUTS := $(HOME)/Library/Keyboard Layouts
KARABINER := $(HOME)/.config/karabiner/assets/complex_modifications
SPIKE_LAYOUT := $(LAYOUTS)/neoneo-spike.keylayout

.PHONY: test dump spike-install spike-uninstall

test:
	python3 -m unittest discover -s tests -v

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
