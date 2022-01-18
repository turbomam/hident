import logging
import click
import click_log
import pandas as pd
import pprint
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

    # def append_id(self, termid):
    #     self.idlist.append(termid)
    #
    # def append_lab(self, lablist):
    #     self.lablist.append(lablist)

    def append_id_lab(self, termid, termlab):
        self.idlist.append(termid)
        self.lablist.append(termlab)

    def add(self, term_id):
        self.termdict[term_id] = Term(term_id)

    def dump(self):
        dumped = {}
        for k, v in self.termdict.items():
            dumped[k] = v.dump()
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
def hident(curie_list, sco_table, lab_table):
    """
    Starting with a list of CURIEs and a dataframe of subclass/superclass relations (full IRIs),
    generate a list of labels with indentation to indicate hierarchy.
    :param curie_list:
    :param sco_table:
    :param lab_table:
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
    dumped = current_indentables.dump()
    pprint.pprint(dumped)
    # initial_dict = build_initial_dict(cl_data, st_data, lab_data)
    # label_id_dict = {}
    # for k, v in initial_dict.items():
    #     label_id_dict[v['label']] = k
    # label_sorted = dict(sorted(label_id_dict.items(), key=lambda x: x[0].lower()))
    # global completed_ids
    # completed_ids = []
    # global completed_indenteds
    # completed_indenteds = []
    # global indent_level
    # indent_level = 0
    # indent_labels(initial_dict, label_sorted, supers_of_requested)

def indent_from_term(term: Term):
    pass


def tidy_sparql_colnames(sparql_res_frame: pd.DataFrame) -> pd.DataFrame:
    cols = sparql_res_frame.columns
    fixed = [i[1:] for i in cols]
    sparql_res_frame.columns = fixed
    return sparql_res_frame


def contract_iri_col(iri_col: pd.Series) -> pd.Series:
    iri_list = list(iri_col)
    curie_list = [pc.contract_uri(i)[0] for i in iri_list]
    return pd.Series(curie_list)


# def indent_labels(initial_dict: dict, label_sorted: dict, supers_of_requested: dict):
#     # global completed_ids
#     global completed_indenteds
#     global indent_level
#     # haven't applied recursion yet
#     for k, v in label_sorted.items():
#         if v not in supers_of_requested:
#             completed_indenteds.append(k)
#             subs = initial_dict[v]['subs']
#             if len(subs) > 0:
#                 for i in subs:
#                     sub_lab = initial_dict[i]['label']
#                     completed_indenteds.append("    " + sub_lab)
#     pprint.pprint(completed_indenteds)


# def set_to_sorted_list(term_set: set[str]) -> list[str]:
#     listified = list(term_set)
#     listified.sort()
#     return listified


# def build_initial_dict(curie_set: set, contracted_frame: pd.DataFrame, label_frame: pd.DataFrame) -> dict:
#     by_super = {}
#     curie_list = list(curie_set)
#     for i in curie_list:
#         current_label = label_frame.loc[label_frame['class'].eq(i), 'label']
#         current_label = current_label.squeeze()
#         subs = contracted_frame.loc[contracted_frame['super'].eq(i) & contracted_frame['sub'].isin(curie_list), 'sub']
#         subs = list(set(list(subs)))
#         by_super[i] = {"label": current_label, "subs": subs}
#     return by_super


# def trim_known_leaves(initial_dict: dict) -> dict:
#     trimmed_dict = initial_dict.copy()
#     for k, v in initial_dict.items():
#         for i in v:
#             if i in initial_dict:
#                 i_list = initial_dict[i]
#                 if len(i_list) == 0:
#                     del trimmed_dict[i]
#     return trimmed_dict


# def iri_frame_to_curie_frame(iri_frame: pd.DataFrame) -> pd.DataFrame:
#     iri_dict = iri_frame.to_dict(orient="records")
#     contracted = []
#     for i in iri_dict:
#         contracted.append({"sub": pc.contract_uri(i["sub"])[0], "super": pc.contract_uri(i["super"])[0]})
#     contracted = pd.DataFrame(contracted)
#     return contracted


if __name__ == "__main__":
    hident()
