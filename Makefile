.PHONY: all clean tests dep_check

all: clean dep_check tests target/envo_sco.tsv target/envo_labs.tsv tests/data/envo_sco.tsv target/hident_conf.txt

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

target/envo_labs.tsv: downloads/envo.owl
	robot query --input $< --query sparql/labels.sparql $@

target/hident_conf.txt: target/envo_sco.tsv target/envo_labs.tsv
	poetry run hident \
		--curie_list tests/data/termlist.txt \
		--sco_table target/envo_sco.tsv \
		--lab_table target/envo_labs.tsv > $@
