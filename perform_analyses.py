import os
from copy import copy

import json
import yaml

import numpy as np
import pandas as pd

from analysis_tools import *


##### Data import and setup #####

# set session
session = 21

# set main data directory
data_super_dir = "../data/"

# set up subdirectories and filepaths
scrape_data_dir = data_super_dir
bill_subdir = "bills"
member_info_filename = f"member_info_data_session{session}.json"
member_reps_filename = "member_replacements.yaml"

# processed_data_dir = os.path.join(data_super_dir, "processed/")
processed_data_dir = "ignore/"
processed_bill_data_filename = f"bill_data_session{session}.json"
processed_vote_data_filename = f"member_vote_data_session{session}.csv"
processed_committee_data_filename = f"committee_bill_data_session{session}.csv"

member_reps_filepath = os.path.join(data_super_dir, member_reps_filename)
member_info_filepath = os.path.join(scrape_data_dir, member_info_filename)
bill_dir = os.path.join(scrape_data_dir, bill_subdir)
processed_bill_data_filepath = os.path.join(
    processed_data_dir, processed_bill_data_filename
)
processed_vote_data_filepath = os.path.join(
    processed_data_dir, processed_vote_data_filename
)
processed_committee_data_filepath = os.path.join(
    processed_data_dir, processed_committee_data_filename
)


# import member list
print("Reading member data")
assert os.path.isfile(member_info_filepath)
with open(member_info_filepath, "r") as f:
    member_info_data = json.load(f)
member_ids = sorted(member_info_data.keys())

# import member vote data
member_vote_df_full = pd.read_csv(processed_vote_data_filepath)
member_n = len(member_vote_df_full.columns) - 1
bill_ids_member = list(member_vote_df_full["bill_id"])
member_ids_in_df = sorted(
    [x for x in list(member_vote_df_full.columns) if x != "bill_id"]
)
assert set(member_ids) == set(member_ids_in_df)
member_vote_df = member_vote_df_full[member_ids]  # remove bill_id column

# import committee data
committee_bill_df_full = pd.read_csv(processed_committee_data_filepath)
committee_n = len(committee_bill_df_full.columns) - 1
bill_ids_committee = list(committee_bill_df_full["bill_id"])
committees = sorted([x for x in list(committee_bill_df_full.columns) if x != "bill_id"])
committee_bill_df = committee_bill_df_full[committees]  # remove bill_id column

# import bill data
print("Reading bill data")
assert os.path.isfile(processed_bill_data_filepath)
with open(processed_bill_data_filepath, "r") as f:
    bill_data = json.load(f)
bill_ids = [x["bill_id"] for x in bill_data]
bill_n = len(bill_ids)

# ensure that bill data is in the correct order
assert all([x == y for x, y in zip(bill_ids, bill_ids_member)])
assert all([x == y for x, y in zip(bill_ids, bill_ids_committee)])


# import member replacement data and validate it
# TODO: ignore invalid data instead of dying?
assert os.path.isfile(member_reps_filepath)

with open(member_reps_filepath, "r") as f:
    input_member_reps_datas = yaml.safe_load(f)

member_reps_dict = {}
for mrd in input_member_reps_datas:
    if str(mrd["session"]) == str(session):
        for this_mr in mrd["data"]:
            this_id = str(this_mr["member_id"])
            this_name = this_mr["name"]

            assert this_id in member_info_data
            assert member_info_data[this_id]["name"] == this_name
            member_reps_dict[this_id] = this_mr
        break


##### Compute means and party differences #####

# List parties
parties = sorted(list(set([member_info_data[x]["party"] for x in member_ids])))
members_by_party = {
    party: [x for x in member_ids if member_info_data[x]["party"] == party]
    for party in parties
}

# Compute party data for each bill
# 1) mean
# 2) sign of mean (is most of party for or against)
# 3) number and percent of party members voting (in any direction)
# Note: we ignore missing votes, but abstentions are 0
party_mean_df = pd.DataFrame(
    {party: member_vote_df[members_by_party[party]].mean(axis=1) for party in parties},
    columns=parties,
)
party_sign_df = party_mean_df.applymap(np.sign)

member_didvote_df = member_vote_df.applymap(lambda x: int(not np.isnan(x)))
party_numvoted_df = pd.DataFrame(
    {
        party: member_didvote_df[members_by_party[party]].sum(axis=1)
        for party in parties
    },
    columns=parties,
)
party_percvoted_df = pd.DataFrame(
    {
        party: member_didvote_df[members_by_party[party]].sum(axis=1)
        / len(members_by_party[party])
        for party in parties
    },
    columns=parties,
)
