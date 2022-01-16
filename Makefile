.PHONY: all clean tests dep_check

all: clean dep_check tests downloads/envo.owl

clean:
	rm -rf downloads/*
	rm -rf target/*

tests:
	poetry run pytest

dep_check:
	robot --version

downloads/envo.owl:
	# --location (-L) pursues redirects
	curl --location http://purl.obolibrary.org/obo/envo.owl -o $@

target/mimimal.tsv: downloads/envo.owl
	robot query --input $< --query sparql/minimal.sparql $@
