# Utilisation :  make html     (le résultat est dans _build/html/index.html)
SPHINXBUILD ?= sphinx-build
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: help html clean
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)"

html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

clean:
	rm -rf $(BUILDDIR)
