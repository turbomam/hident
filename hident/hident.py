import logging
import click
import click_log
import pandas as pd
# import pprint
import prefixcommons as pc

# need tests on sco and label frames

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


# # for recursion
# completed_ids = []
# completed_indenteds = []
# indent_level = 0


class Term:
    def __init__(self, term_id):
        self.term_id = term_id
        self.term_lab = None
        self.supers = []
        self.subs = []
        self.next = None

    def apply_label(self, term_lab):
        self.term_lab = term_lab

    def apply_subs(self, subs):
        self.subs = subs

    def apply_supers(self, supers):
        self.supers = supers

    # def get_attrib(self, attrib):
    #     return self[attrib]

    def dump(self):
        dumped = {
            "term_id": self.term_id,
            "term_lab": self.term_lab,
            "supers": self.supers,
            "subs": self.subs
        }
        return dumped


# assert a type for the term dict?
class Indentables:
    def __init__(self):
        self.termdict = {}
        self.idlist = []
        self.lablist = []
        self.roots = []
        self.leaves = []

    def determine_roots(self):
        for k, v in self.termdict.items():
            temp = v.dump()
            if len(temp['supers']) == 0:
                self.roots.append(k)

    def determine_leaves(self):
        for k, v in self.termdict.items():
            temp = v.dump()
            if len(temp['subs']) == 0:
                self.leaves.append(k)

    def get_roots(self) -> list[str]:
        return self.roots

    def get_leaves(self) -> list[str]:
        return self.leaves

    def append_id_lab(self, termid, termlab):
        self.idlist.append(termid)
        self.lablist.append(termlab)

    def get_ids_labs(self) -> pd.DataFrame:
        ids = self.idlist
        labs = self.lablist
        id_lab_frame = pd.concat([pd.Series(ids, name='id'), pd.Series(labs, name='indented_lab')], axis=1)
        return id_lab_frame

    def add(self, term_id):
        self.termdict[term_id] = Term(term_id)

    def dump(self) -> dict:
        dumped = {}
        for k, v in self.termdict.items():
            dumped[k] = v.dump()
        return dumped

    def dump_term(self, term_id) -> dict:
        dumpsource = self.termdict[term_id]
        dumped = dumpsource.dump()
        return dumped

    def apply_label(self, term_id, term_lab):
        temp = self.termdict[term_id]
        temp.apply_label(term_lab)
        self.termdict[term_id] = temp

    def apply_subs(self, term_id, subs):
        temp = self.termdict[term_id]
        temp.apply_subs(subs)
        self.termdict[term_id] = temp

    def apply_supers(self, term_id, supers):
        temp = self.termdict[term_id]
        temp.apply_supers(supers)
        self.termdict[term_id] = temp


@click.command()
@click_log.simple_verbosity_option(logger)
@click.option('--curie_list', type=click.Path(exists=True), required=True, help="headerless list of term ids")
@click.option('--sco_table', type=click.Path(exists=True), required=True,
              help="subclass table with IRIs, from sparql/sco.sparql")
@click.option('--lab_table', type=click.Path(exists=True), required=True,
              help="label table with IRIs, from sparql/labels.sparql")
@click.option('--indented_tsv', type=click.Path(), required=True,
              help="output TSV file")
def hident(curie_list, sco_table, lab_table, indented_tsv):
    """
    Starting with a list of CURIEs and a dataframe of subclass/superclass relations (full IRIs),
    generate a list of labels with indentation to indicate hierarchy.
    :param curie_list:
    :param sco_table:
    :param lab_table:
    :param indented_tsv:
    :return:
    """
    current_indentables = Indentables()
    cl_data = pd.read_csv(curie_list, header=None)
    cl_data = set(cl_data[0])
    st_data = pd.read_csv(sco_table, sep="\t")
    st_data = tidy_sparql_colnames(st_data)
    st_data['sub'] = contract_iri_col(st_data['sub'])
    st_data['super'] = contract_iri_col(st_data['super'])
    lab_data = pd.read_csv(lab_table, sep="\t")
    lab_data = tidy_sparql_colnames(lab_data)
    lab_data['class'] = contract_iri_col(lab_data['class'])
    for i in cl_data:
        current_indentables.add(i)
        # assuming single label?
        current_label = lab_data.loc[lab_data['class'].eq(i), 'label']
        current_label = current_label.squeeze()
        current_indentables.apply_label(i, current_label)
        current_subs = list(st_data.loc[st_data['super'].eq(i) & st_data['sub'].isin(cl_data), 'sub'])
        current_supers = list(st_data.loc[st_data['sub'].eq(i) & st_data['super'].isin(cl_data), 'super'])
        current_indentables.apply_subs(i, current_subs)
        current_indentables.apply_supers(i, current_supers)
    # dumped = current_indentables.dump()
    current_indentables.determine_roots()
    roots = current_indentables.get_roots()
    for i in roots:
        indent_from_term(i, current_indentables, 0)
    id_lab_frame = current_indentables.get_ids_labs()
    # left_aligned_ilf = id_lab_frame.style.set_properties(**{'text-align': 'left'})
    id_lab_frame.to_csv(indented_tsv, sep="\t", index=False)


def indent_from_term(term_id: str, indentable: Indentables, indent_level: int):
    padding = "  " * indent_level
    if term_id in indentable.leaves:
        return
    else:
        term_dict = indentable.dump_term(term_id)
        term_lab = term_dict['term_lab']
        indented_lab = padding + term_lab
        indentable.append_id_lab(term_id, indented_lab)
        subs = term_dict['subs']
        for i in subs:
            new_indent_level = indent_level + 1
            indent_from_term(i, indentable, new_indent_level)


def tidy_sparql_colnames(sparql_res_frame: pd.DataFrame) -> pd.DataFrame:
    cols = sparql_res_frame.columns
    fixed = [i[1:] for i in cols]
    sparql_res_frame.columns = fixed
    return sparql_res_frame


def contract_iri_col(iri_col: pd.Series) -> pd.Series:
    iri_list = list(iri_col)
    curie_list = [pc.contract_uri(i)[0] for i in iri_list]
    return pd.Series(curie_list)


def set_to_sorted_list(term_set: set[str]) -> list[str]:
    listified = list(term_set)
    listified.sort()
    return listified


if __name__ == "__main__":
    hident()
