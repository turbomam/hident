.PHONY: all clean tests dep_check micro_clean

all: clean dep_check tests target/soils_indented.tsv

clean:
	rm -rf downloads/*.owl
	rm -rf target/*.tsv

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

micro_clean:
	rm -rf target/soils_indented.tsv

target/soils_indented.tsv: target/envo_sco.tsv target/envo_labs.tsv
	poetry run hident \
		--curie_file_name tests/data/soil_ebs_curated_termlist.txt \
		--sco_tab_file_name target/envo_sco.tsv \
		--lab_tab_file_name target/envo_labs.tsv \
		--pad_char _ \
		--pad_count 2 \
		--parent_term 'broad-scale environmental context' \
		--indented_tsv $@ > $@
