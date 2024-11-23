# You can set these variables from the command line, and also
# from the environment for the first two.
DOCBUILD   ?= mkdocs
SOURCEDIR     = .
APP = /app

.PHONY: help livehtml Makefile

# Put it first so that "make" without argument is like "make help".
help:
	@$(DOCBUILD) -h "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Build, watch and serve docs with live reload
livehtml:
	@$(DOCBUILD) serve -w $(SOURCEDIR)

# Catch-all target: route all unknown targets to build
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(DOCBUILD) build
