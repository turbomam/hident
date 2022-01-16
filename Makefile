.PHONY: all clean tests dep_check

all: clean dep_check tests target/envo_sco.tsv

clean:
	rm -rf downloads/*
	rm -rf target/*

tests:
	poetry run pytest

dep_check:
	java -version
	robot --version

downloads/envo.owl:
	# --location (-L) pursues redirects
	curl --location http://purl.obolibrary.org/obo/envo.owl -o $@

target/envo_sco.tsv: downloads/envo.owl
	robot query --input $< --query sparql/sco.sparql $@
