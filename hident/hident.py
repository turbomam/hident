import logging
import click
import click_log
import pandas as pd
# import pprint
import prefixcommons as pc

# need tests on sco and label frames

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


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
        self.requesteds = []
        self.sco_frame = None
        self.label_frame = None

    def determine_roots(self):
        for k, v in self.termdict.items():
            temp = v.dump()
            if len(temp['supers']) == 0:
                self.roots.append(k)

    def determine_leaves(self):
        for k, v in self.termdict.items():
            temp = v.dump()
            if len(temp['subs']) == 0 and len(temp['supers']) > 0:
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

    def requesteds_from_txt_file(self, textfile_name: str, colnum=0, header=None):
        # assuming they're curies
        requesteds_frame = pd.read_csv(textfile_name, header=header)
        requesteds = set(requesteds_frame[colnum])
        logger.debug(requesteds)
        self.requesteds = list(requesteds)

    def alphabetize_terms(self, term_list) -> list:
        lf = self.label_frame
        lf = lf.loc[lf['class'].isin(term_list)]
        lf = lf.sort_values(by='label')
        alphabetized = list(lf['class'])
        # logger.info(lf)
        return alphabetized

    def alphabetize_requesteds(self):
        term_list = self.requesteds
        alphabetized = self.alphabetize_terms(term_list)
        self.requesteds = alphabetized

    def prepare_frame(self, frame_file_name: str, cols_to_tidy: list[str], header=1, sep="\t") -> pd.DataFrame:
        # assuming they're full IRIs (but without < or >
        logger.debug(frame_file_name)
        frame = pd.read_csv(frame_file_name, header=header, sep=sep)
        logger.debug(frame)
        tidy = tidy_sparql_colnames(frame)
        logger.debug(tidy)
        for i in cols_to_tidy:
            logger.debug(i)
            tidy[i] = contract_iri_col(tidy[i])
        logger.debug(tidy)
        return tidy

    def sco_from_txt_file(self, sco_file_name, header=0):
        sco_frame = self.prepare_frame(sco_file_name, ['sub', 'super'], header=header)
        self.sco_frame = sco_frame

    def labs_from_txt_file(self, labs_file_name, header=0):
        sco_frame = self.prepare_frame(labs_file_name, ['class'], header=header)
        self.label_frame = sco_frame

    def load_term(self, term_id):
        self.add(term_id)
        # assuming single label?
        label_frame = self.label_frame
        current_label = label_frame.loc[label_frame['class'].eq(term_id), 'label']
        current_label = current_label.squeeze()
        self.apply_label(term_id, current_label)
        sco_frame = self.sco_frame
        current_subs = list(
            sco_frame.loc[sco_frame['super'].eq(term_id) & sco_frame['sub'].isin(self.requesteds), 'sub'])
        current_supers = list(
            sco_frame.loc[sco_frame['sub'].eq(term_id) & sco_frame['super'].isin(self.requesteds), 'super'])
        self.apply_subs(term_id, current_subs)
        self.apply_supers(term_id, current_supers)

    def load_all_terms(self):
        for i in self.requesteds:
            self.load_term(i)

    def indent_from_term(self, term_id: str, indent_level: int):
        padding = "  " * indent_level
        if term_id in self.leaves:
            return
        else:
            term_dict = self.dump_term(term_id)
            term_lab = term_dict['term_lab']
            indented_lab = padding + term_lab
            self.append_id_lab(term_id, indented_lab)
            subs = term_dict['subs']
            subs = self.alphabetize_terms(subs)
            for i in subs:
                new_indent_level = indent_level + 1
                self.indent_from_term(i, new_indent_level)

    def wrapper(self):
        self.load_all_terms()
        # dumped = self.dump()
        # pprint.pprint(dumped)
        self.determine_roots()
        # roots = self.get_roots()
        for i in self.roots:
            self.indent_from_term(i, 0)


@click.command()
@click_log.simple_verbosity_option(logger)
@click.option('--curie_file_name', type=click.Path(exists=True), required=True, help="headerless list of term ids")
@click.option('--sco_tab_file_name', type=click.Path(exists=True), required=True,
              help="subclass table with IRIs, from sparql/sco.sparql")
@click.option('--lab_tab_file_name', type=click.Path(exists=True), required=True,
              help="label table with IRIs, from sparql/labels.sparql")
@click.option('--indented_tsv', type=click.Path(), required=True,
              help="output TSV file")
def hident(curie_file_name, sco_tab_file_name, lab_tab_file_name, indented_tsv):
    """
    Starting with a list of CURIEs and a dataframe of subclass/superclass relations (full IRIs),
    generate a list of labels with indentation to indicate hierarchy.
    :param curie_file_name:
    :param sco_tab_file_name:
    :param lab_tab_file_name:
    :param indented_tsv:
    :return:
    """
    current_indentables = Indentables()
    current_indentables.requesteds_from_txt_file(curie_file_name)
    current_indentables.sco_from_txt_file(sco_tab_file_name)
    current_indentables.labs_from_txt_file(lab_tab_file_name)
    current_indentables.alphabetize_requesteds()
    current_indentables.wrapper()
    id_lab_frame = current_indentables.get_ids_labs()
    # # left_aligned_ilf = id_lab_frame.style.set_properties(**{'text-align': 'left'})
    id_lab_frame.to_csv(indented_tsv, sep="\t", index=False)


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
